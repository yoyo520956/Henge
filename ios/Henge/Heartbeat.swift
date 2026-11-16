// SPDX-License-Identifier: GPL-2.0-or-later
import BackgroundTasks
import Combine
import Darwin
import Foundation
import UIKit

/// Henge's five-minute heartbeat.
///
/// Why it exists: on a 4 GB phone the guest Mac, the JIT code region and Henge
/// itself share real RAM with iOS, and jetsam kills whichever process is
/// largest when memory runs short. A Mac left running for hours slowly
/// accumulates state the guest never gives back (the translation layer's
/// blocks, the display's frame buffers, the log), and the first symptom is
/// iOS closing Henge mid-session rather than a visible failure.
///
/// So every five minutes Henge checks itself: how much memory it holds, how
/// much the Mac holds, whether the guest is still healthy, and whether the log
/// has grown past what is useful. Nothing destructive happens -- the heartbeat
/// only observes and trims what Henge owns (the log, caches) and reports.
///
/// iOS does not promise to wake a suspended app on a schedule, and it will not
/// keep a background task alive indefinitely. The in-app timer is exact while
/// Henge is on screen, which is when the Mac is running and when the memory
/// matters; BGTaskScheduler is a best-effort second line for the case where
/// Henge is backgrounded. The heartbeat records what it actually managed to do,
/// so the log shows the gaps instead of pretending they did not happen.
enum Heartbeat {

    /// The interval the user asked for.
    static let interval: TimeInterval = 5 * 60

    /// BGTaskScheduler identifier, registered in Info.plist under
    /// BGTaskSchedulerPermittedIdentifiers.
    static let backgroundTaskID = "com.henge.app.heartbeat"

    /// A single round's result, kept so the app can show it and so the next
    /// round can back off if this one failed.
    struct Round {
        var startedAt = Date()
        var finishedAt = Date()
        var memoryMB: Int = 0
        var guestRAMMB: Int = 0
        var vmState: Int = 0
        var logBytes: Int = 0
        var trimmedLogBytes: Int = 0
        var ok = true
        var note: String = ""
    }

    /// Everything the heartbeat knows, readable from the UI and the log.
    /// The heartbeat is an observable object so the settings page can show the
    /// last round without polling it.
    final class HeartbeatObserver: ObservableObject {
        @Published var lastRound: Round?
    }

    static let observer = HeartbeatObserver()

    /// How many rounds have run since launch. Guarded by the lock: rounds run
    /// on a background queue, and the count is read from the log line too.
    static var roundCount: Int {
        lock.lock(); defer { lock.unlock() }
        return _roundCount
    }
    private static var _roundCount = 0

    /// Consecutive failures, used for the backoff.
    static var consecutiveFailures: Int {
        lock.lock(); defer { lock.unlock() }
        return _consecutiveFailures
    }
    private static var _consecutiveFailures = 0

    /// The timer's own queue, so a round never runs on the main thread.
    private static let queue = DispatchQueue(label: "com.henge.app.heartbeat", qos: .utility)

    private static var timer: DispatchSourceTimer?
    private static var registered = false
    private static let lock = NSLock()

    // MARK: - Lifecycle

    /// Start the heartbeat. Safe to call more than once.
    static func start() {
        lock.lock()
        defer { lock.unlock() }
        guard !registered else { return }
        registered = true

        registerBackgroundTask()
        scheduleTimer()

        HengeLog.log("heartbeat", "started: every \(Int(interval / 60)) minutes, "
                    + "low-memory profile \(L.s(LowMemoryProfile.active.key))")
    }

    /// Stop the heartbeat. Used when the app is told to stop working.
    static func stop() {
        lock.lock()
        defer { lock.unlock() }
        timer?.cancel()
        timer = nil
        registered = false
        HengeLog.log("heartbeat", "stopped")
    }

    /// (Re)arm the timer. Called when the app comes back to the foreground:
    /// a timer that was suspended while Henge was in the background fires late,
    /// and the point of the heartbeat is that the gap is small.
    static func appDidBecomeActive() {
        lock.lock()
        defer { lock.unlock() }
        guard registered else { return }
        scheduleTimer()
        HengeLog.log("heartbeat", "foreground: timer re-armed")
    }

    /// The app is going to the background. Ask the system for a window in which
    /// to run one more round.
    static func appDidEnterBackground() {
        scheduleBackgroundRound()
    }

    // MARK: - The timer

    private static func scheduleTimer() {
        timer?.cancel()
        let source = DispatchSource.makeTimerSource(queue: queue)
        // A little slack on the start so a timer that was rescheduled does not
        // fire in a burst with the old one.
        source.schedule(deadline: .now() + interval, repeating: interval, leeway: .seconds(30))
        source.setEventHandler { runRound(reason: "timer") }
        source.resume()
        timer = source
    }

    // MARK: - Background task

    /// Register the background refresh. Registration must happen before the app
    /// finishes launching, so this is called from HengeApp.init().
    private static func registerBackgroundTask() {
        BGTaskScheduler.shared.register(forTaskWithIdentifier: backgroundTaskID, using: nil) { task in
            guard let refresh = task as? BGAppRefreshTask else {
                task.setTaskCompleted(success: false)
                return
            }
            self.handleBackgroundRefresh(refresh)
        }
    }

    private static func handleBackgroundRefresh(_ task: BGAppRefreshTask) {
        // The system gave us a window; use it and ask for the next one.
        scheduleBackgroundRound()

        var finished = false
        task.expirationHandler = {
            guard !finished else { return }
            finished = true
            HengeLog.log("heartbeat", "background window expired before the round finished")
            task.setTaskCompleted(success: false)
        }

        queue.async {
            let round = performRound(reason: "background")
            finished = true
            task.setTaskCompleted(success: round.ok)
        }
    }

    private static func scheduleBackgroundRound() {
        let request = BGAppRefreshTaskRequest(identifier: backgroundTaskID)
        request.earliestBeginDate = Date(timeIntervalSinceNow: interval)
        do {
            try BGTaskScheduler.shared.submit(request)
            HengeLog.log("heartbeat", "background round requested")
        } catch {
            // BGTaskScheduler refuses on a device without the entitlement, or
            // when the app is not eligible. That is expected outside a real
            // install and must not stop the in-app timer.
            HengeLog.log("heartbeat", "background round not scheduled: \(error.localizedDescription)")
        }
    }

    // MARK: - A round

    /// Run one round. Separate from performRound so the retry logic can call it
    /// again without rescheduling the timer.
    static func runRound(reason: String) {
        lock.lock()
        let failures = _consecutiveFailures
        lock.unlock()

        var round = performRound(reason: reason)
        if round.ok {
            lock.lock()
            _consecutiveFailures = 0
            lock.unlock()
        } else {
            // Exponential backoff, capped at a minute, so a round that keeps
            // failing does not turn into a busy loop on a device that is already
            // short of memory.
            let delay = min(pow(2.0, Double(failures)), 60.0)
            lock.lock()
            _consecutiveFailures += 1
            lock.unlock()
            HengeLog.log("heartbeat", "round failed, retrying in \(Int(delay))s")
            queue.asyncAfter(deadline: .now() + delay) { runRound(reason: reason + "-retry") }
        }

        lock.lock()
        _roundCount += 1
        let count = _roundCount
        lock.unlock()

        let summary = "round \(count): memory \(round.memoryMB) MB, guest \(round.guestRAMMB) MB, "
            + "vm state \(round.vmState), log \(round.logBytes) bytes"
        HengeLog.log("heartbeat", summary + (round.note.isEmpty ? "" : " — \(round.note)"))
        Task { @MainActor in observer.lastRound = round }
    }

    /// What a round actually does. Split out so the retry path and the
    /// background path share it.
    private static func performRound(reason: String) -> Round {
        var round = Round()

        // Ask for a background window so the round is not cut off the moment
        // the user leaves the app.
        var backgroundID = UIBackgroundTaskIdentifier.invalid
        backgroundID = UIApplication.shared.beginBackgroundTask(withName: "Henge heartbeat") {
            if backgroundID != .invalid {
                UIApplication.shared.endBackgroundTask(backgroundID)
                backgroundID = .invalid
            }
        }
        defer {
            if backgroundID != .invalid {
                UIApplication.shared.endBackgroundTask(backgroundID)
            }
        }

        HengeLog.logFootprint("heartbeat")
        round.memoryMB = currentFootprintMB()
        round.vmState = Int(henge_vm_state())
        round.guestRAMMB = guestRAMMB()

        round.logBytes = logFileSize()
        if round.logBytes > logTrimThreshold {
            let trimmed = trimLog(to: logKeepBytes)
            round.trimmedLogBytes = trimmed
            round.note = "trimmed \(trimmed) bytes of log"
        }

        // Flush the log to disk so a crash right after this round still has
        // the round before it in the file.
        HengeLog.flushNow()

        round.finishedAt = Date()
        return round
    }

    // MARK: - Measurements

    /// Henge's own resident footprint, in MB.
    private static func currentFootprintMB() -> Int {
        var info = task_vm_info_data_t()
        var count = mach_msg_type_number_t(MemoryLayout<task_vm_info_data_t>.size / MemoryLayout<natural_t>.size)
        let result = withUnsafeMutablePointer(to: &info) {
            $0.withMemoryRebound(to: integer_t.self, capacity: Int(count)) {
                task_info(mach_task_self_, task_flavor_t(TASK_VM_INFO), $0, &count)
            }
        }
        guard result == KERN_SUCCESS else { return 0 }
        return Int(info.phys_footprint) / (1024 * 1024)
    }

    /// How much RAM the guest Mac was given, in MB. Zero when no Mac runs.
    /// The running Mac tells the heartbeat what it was started with when it
    /// boots, because the engine does not expose the figure and the Mac's own
    /// record holds the configured size rather than the size it is running at.
    private static func guestRAMMB() -> Int {
        guard henge_vm_state() != 0 else { return 0 }
        return runningGuestRAMMB
    }

    /// Set by SessionView when a Mac starts. Protected by the same lock as the
    /// rest of the heartbeat's state.
    static func noteGuestStarted(ramMB: Int) {
        lock.lock()
        runningGuestRAMMB = ramMB
        lock.unlock()
    }

    /// Set by SessionView when a Mac stops.
    static func noteGuestStopped() {
        lock.lock()
        runningGuestRAMMB = 0
        lock.unlock()
    }

    private static var runningGuestRAMMB = 0

    private static func logFileSize() -> Int {
        let url = HengeLog.logFileURL
        let attributes = try? FileManager.default.attributesOfItem(atPath: url.path)
        return (attributes?[.size] as? NSNumber)?.intValue ?? 0
    }

    /// Keep the last `keep` bytes of the log and drop the rest. The log is
    /// Henge's own file, and the part being dropped is the oldest, so this is
    /// safe to do while the app runs.
    private static func trimLog(to keep: Int) -> Int {
        let url = HengeLog.logFileURL
        guard let data = try? Data(contentsOf: url), data.count > keep else { return 0 }
        let tail = data.suffix(keep)
        let temp = url.deletingLastPathComponent().appendingPathComponent("henge.log.trim")
        do {
            try tail.write(to: temp, options: .atomic)
            _ = try FileManager.default.replaceItemAt(url, withItemAt: temp)
            return data.count - keep
        } catch {
            try? FileManager.default.removeItem(at: temp)
            return 0
        }
    }

    /// The log grows by a few hundred kilobytes an hour while a Mac runs.
    /// Past this size it is worth trimming; the tail that is kept is a few
    /// megabytes, which covers the interesting part of a session.
    private static let logTrimThreshold = 8 * 1024 * 1024
    private static let logKeepBytes = 4 * 1024 * 1024
}
