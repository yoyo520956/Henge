import Foundation

/// The performance plan for this device: how many vCPUs the Mac gets, how much RAM it
/// gets, and which engine knobs are set for it. One place, so nothing drifts apart.
///
/// Why the plan exists: a 4 GB phone shares its RAM between iOS, Henge, the JIT code
/// region and the guest Mac. The old defaults (4 vCPUs, a 2 GB Mac) made a Mac that
/// booted but crawled: macOS under 4 GB swaps on every window redraw, and each extra
/// vCPU is a real host thread that competes with the others for the same cores.
/// Fewer vCPUs and a slightly larger guest (backed by a file, whose pages iOS does not
/// count against the app's memory limit) is the trade that actually makes a Mac usable.
enum PerformancePlan {

    /// The vCPU count the Mac runs with. macOS is happy on two: the emulated CPUs are
    /// host threads, and the guest's own scheduler has work to do either way, so extra
    /// cores buy nothing on a phone and cost the cores the display and the JIT need.
    static var cpuCount: Int {
        switch Device.physicalMB {
        case 14_000...: return 4      // 16 GB devices: room for a real Mac
        case 10_000..<14_000: return 4
        case 7_000..<10_000: return 3
        case 5_000..<7_000: return 2
        default: return 2            // 4 GB phones (iPhone SE 3 and the like)
        }
    }

    /// The RAM the Mac gets, in MB. The guest's pages live in a file when the kernel
    /// refuses to leave them out of Henge's footprint, and a mapped file does not count
    /// against iOS's limit for the app, so this can be larger than the phone's own RAM
    /// without iOS killing Henge for it. macOS under 4 GB is slow whatever else is done,
    /// so the low-memory class still gets 3 GB: enough for the desktop and a couple of
    /// small apps, and the swap it does is to a file rather than to a stalled phone.
    static var guestRAMMB: Int {
        switch Device.physicalMB {
        case 14_000...: return 8 * 1024
        case 10_000..<14_000: return 6 * 1024
        case 7_000..<10_000: return 4 * 1024
        case 5_000..<7_000: return 3 * 1024
        default: return 3 * 1024      // 4 GB phones
        }
    }

    /// The refresh rate macOS is told the display has. Every frame is emulated and
    /// replayed, so on a phone that is short of both CPU and memory, 30 Hz leaves more
    /// for the guest and the animation still reads as smooth on a small screen.
    static var refreshRate: Int {
        Device.lowMemory ? 30 : 60
    }

    /// The JIT code cache. It is memory the guest cannot have while the cache holds it,
    /// so a tight phone gets the small one.
    static var codeCacheMB: Int {
        switch Device.physicalMB {
        case 14_000...: return 1536
        case 10_000..<14_000: return 1024
        default: return 512
        }
    }

    /// The temporary Mac the installer boots to run macOS's own restore. The restore
    /// is a burst of work, so it gets what it needs where there is room.
    static var restoreCapMB: Int {
        Device.lowMemory ? 3072 : 4096
    }

    /// Whether the idle vCPUs spin instead of sleeping. Spinning trades battery and
    /// phone heat for a few microseconds of wake-up latency, and with more than one
    /// vCPU every idle core spins too: on a 4 GB phone that heat is what makes the
    /// display stutter. Off: the guest's wake-ups are worth more than the battery.
    static var spinIdleCPUs: Bool { !Device.lowMemory }

    /// The engine settings this plan implies, on top of EngineTuning's own defaults.
    /// Applied at launch and before each Mac starts.
    static func applyEngineSettings() {
        setenv("HV_HZ", String(refreshRate), 1)
        if spinIdleCPUs {
            setenv("HV_WFI_SPIN", "50", 1)
        } else {
            unsetenv("HV_WFI_SPIN")
        }
        HengeLog.log("plan", "\(cpuCount) vCPU, \(guestRAMMB / 1024) GB guest RAM, \(refreshRate) Hz, "
                    + "\(codeCacheMB) MB code cache, idle spin \(spinIdleCPUs ? "on" : "off")")
    }

    /// A line for the log and the UI, so what the Mac runs with is never a mystery.
    static var summary: String {
        L.f("%lld vCPU, %lld GB", cpuCount, guestRAMMB / 1024)
    }
}
