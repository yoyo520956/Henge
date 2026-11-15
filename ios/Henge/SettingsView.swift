import SwiftUI

struct SettingsView: View {
    @ObservedObject private var jit = JITCoordinator.shared
    @AppStorage(JITCoordinator.autoEnableKey) private var jitAtLaunch = false
    @AppStorage(HardwareMouse.speedKey) private var mouseSpeed = 1.0
    @AppStorage(HardwareMouse.reverseKey) private var reverseScrolling = false
    @AppStorage(HardwareMouse.scrollSpeedKey) private var scrollSpeed = 0.3
    @AppStorage(VolumeClicks.inputModeKey) private var inputMode = VolumeClicks.InputMode.touchscreen
    @AppStorage(VolumeClicks.modeKey) private var volumeMode = VolumeClicks.Mode.delayHold
    @AppStorage(VolumeClicks.swapKey) private var swapButtons = false
    @AppStorage(PhysicalMouseButtons.swapKey) private var swapMouseButtons = false
    @AppStorage(EngineTuning.refreshKey) private var refreshRate = 60
    @AppStorage(EngineTuning.fastFlushKey) private var fastFlush = true
    @AppStorage(EngineTuning.wfiSpinKey) private var wfiSpin = false
    @AppStorage(EngineTuning.superblocksKey) private var superblocks = false
    @AppStorage(JITBootstrap.codeCacheKey) private var codeCacheMB = JITBootstrap.defaultCodeCacheMB
    @AppStorage(LowMemoryProfile.modeKey) private var memoryProfile = 0
    @AppStorage(DeskAppearance.key) private var appearance = DeskAppearance.system
    @AppStorage(InstantResume.key) private var instantResume = false
    @AppStorage(MacAppsFeature.key) private var macApps = false
    /// The heartbeat's last round, shown in the Heartbeat section.
    @ObservedObject private var heartbeat = Heartbeat.observer

    /// The second footer paragraph: how you click, given the selected input mode.
    private var inputDescription: String {
        if inputMode == .touchscreen {
            return L.s("Tap to click once. Tap then hold to begin dragging. Quickly tap with two fingers to right-click.")
        }
        switch volumeMode {
        case .delayHold:
            return L.s("Delay hold waits to see if you're holding or just clicking the volume button, which results in all clicks being ~0.5s long.")
        case .tapThenDrag:
            return L.s("Tap then drag waits to see if you're holding or just clicking the volume button, but it unconditionally sends a single click regardless of whether you tap or hold, which results in shorter clicks at the cost of sending a click before holding.")
        case .intercept:
            return L.s("Activates the camera in order to intercept volume keys properly. This causes the volume keys to behave in the same way a mouse's buttons do, but it causes higher temperatures, as the camera is always on.")
        }
    }

    var body: some View {
        NavigationStack {
            Form {
                Section(L.s("JIT")) {
                    LabeledContent("Status", value: JITBootstrap.ready ? L.s("On") : L.s("Off"))
                    Picker(L.s("Method"), selection: $jit.method) {
                        ForEach(JITMethod.allCases) { Text($0.title).tag($0) }
                    }
                    Text(jit.method == .automatic ? jit.automaticDescription : L.f("Henge uses %@.", jit.method.title))
                        .font(.footnote).foregroundStyle(.secondary)
                    Button(L.s("Set up JIT")) { jit.showSetup = true }
                    Toggle(L.s("Turn on JIT when Henge opens"), isOn: $jitAtLaunch)
                    if jitAtLaunch {
                        Text(L.s("Henge connects LocalDevVPN first when it is off, and comes back."))
                            .font(.footnote).foregroundStyle(.secondary)
                    }
                    LabeledContent(L.s("Code region"), value: L.f("%lld MB, claimed once per launch", JITBootstrap.jitBytes >> 20))
                }
                .listRowBackground(Desk.card)
                Section(L.s("Memory")) {
                    LabeledContent(L.s("Extra memory"), value: Entitlements.increasedMemory ? L.s("On") : L.s("Off"))
                    LabeledContent(L.s("Henge's limit"), value: ByteText.string(UInt64(Entitlements.memoryLimitAtLaunch)))
                    LabeledContent(L.s("Free for Henge"), value: ByteText.string(UInt64(henge_available_memory())))
                    Text(Entitlements.increasedMemory
                         ? L.s("A Mac's memory is kept out of this limit once JIT is on. If iOS refuses that, it uses free storage instead.")
                         : L.s("This install isn't signed with the increased memory limit entitlement. Reinstall Henge with a certificate that has it. Export your Mac first if the reinstall replaces the app's data."))
                        .font(.footnote).foregroundStyle(.secondary)
                }
                .listRowBackground(Desk.card)
                Section(L.s("Memory profile")) {
                    Picker(L.s("Profile"), selection: $memoryProfile) {
                        ForEach([LowMemoryProfile.Mode.auto, .low, .balanced, .performance]) { Text(L.s($0.key)).tag($0.rawValue) }
                    }
                    .pickerStyle(.menu)
                    LabeledContent(L.s("Active profile"), value: L.s(LowMemoryProfile.active.key))
                    LabeledContent(L.s("Recommended Mac memory"), value: L.f("%lld GB", Device.suggestedRAMGB))
                    Text(LowMemoryProfile.active == .low
                         ? L.s("The device is short of memory, or this install's limit is under 3 GB: Henge picks a 512 MB code cache and a 30 Hz display by default, and caps the installer's temporary Mac at 2 GB. A 2 GB Mac is the most this device is likely to keep up. Choose a larger cache only if the Mac closes Henge mid-setup.")
                         : L.s("Auto picks the code cache and refresh rate the device has room for. Changes apply the next time a Mac starts."))
                        .font(.footnote).foregroundStyle(.secondary)
                }
                .listRowBackground(Desk.card)
                Section(L.s("Heartbeat")) {
                    LabeledContent(L.s("Check interval"), value: L.f("%lld minutes", Int(Heartbeat.interval / 60)))
                    LabeledContent(L.s("Checks so far"), value: L.f("%lld", Heartbeat.roundCount))
                    if let round = heartbeat.lastRound {
                        LabeledContent(L.s("Henge's memory"), value: L.f("%lld MB", round.memoryMB))
                        LabeledContent(L.s("Mac's memory"), value: L.f("%lld MB", round.guestRAMMB))
                        LabeledContent(L.s("Last check"),
                                       value: round.finishedAt.formatted(date: .omitted, time: .standard))
                        if !round.note.isEmpty {
                            Text(round.note).font(.footnote).foregroundStyle(.secondary)
                        }
                    }
                    Text(L.s("Every few minutes Henge checks its own memory, the running Mac's memory and its log, and trims the log when it grows too large. This keeps iOS from closing Henge on a phone with little memory. iOS decides when a backgrounded app may run, so the checks are exact while Henge is open and best-effort when it is not."))
                        .font(.footnote).foregroundStyle(.secondary)
                }
                .listRowBackground(Desk.card)
                if Device.isPad {
                    Section(L.s("Mouse and Trackpad")) {
                        VStack(alignment: .leading, spacing: 4) {
                            Text(L.s("Pointer speed"))
                            Slider(value: $mouseSpeed, in: 0.5...3)
                        }
                        Toggle(L.s("Reverse scrolling"), isOn: $reverseScrolling)
                        VStack(alignment: .leading, spacing: 4) {
                            Text(L.s("Scroll speed"))
                            Slider(value: $scrollSpeed, in: 0.1...1.5)
                        }
                        Toggle(L.s("Swap physical right and middle buttons"), isOn: $swapMouseButtons)
                        Text(L.s("Only enable this if your physical mouse's right and middle buttons are reversed in the Mac. Touch controls stay unchanged. Restart the Mac session to apply."))
                            .font(.footnote).foregroundStyle(.secondary)
                        Text(L.s("A Magic Keyboard or a Bluetooth mouse moves the Mac's pointer. Pointer speed changes apply the next time a Mac starts; scroll speed changes apply immediately."))
                            .font(.footnote).foregroundStyle(.secondary)
                    }
                    .listRowBackground(Desk.card)
                }
                if !Device.isPad {
                    Section(L.s("Trackpad")) {
                        Picker(L.s("Input mode"), selection: $inputMode) {
                            Text(L.s("Touchscreen")).tag(VolumeClicks.InputMode.touchscreen)
                            Text(L.s("Volume buttons")).tag(VolumeClicks.InputMode.volumeButtons)
                        }
                        .pickerStyle(.menu)
                        if inputMode == .volumeButtons {
                            Picker(L.s("Button mode"), selection: $volumeMode) {
                                Text(L.s("Delay hold")).tag(VolumeClicks.Mode.delayHold)
                                Text(L.s("Tap then drag")).tag(VolumeClicks.Mode.tapThenDrag)
                                Text(L.s("Camera intercept")).tag(VolumeClicks.Mode.intercept)
                            }
                            .pickerStyle(.menu)
                            Toggle(L.s("Swap buttons"), isOn: $swapButtons)
                        }
                        Text(L.f("Henge is able to emulate a Magic Trackpad, allowing you to perform native macOS gestures using your device's touchscreen.\n\n%@", inputDescription))
                            .font(.footnote).foregroundStyle(.secondary)
                    }
                    .listRowBackground(Desk.card)
                }
                Section(L.s("Performance")) {
                    Picker(L.s("Mac refresh rate"), selection: $refreshRate) {
                        Text(L.s("30 Hz")).tag(30)
                        Text(L.s("60 Hz")).tag(60)
                        Text(L.s("120 Hz")).tag(120)
                    }
                    .pickerStyle(.segmented)
                    Toggle(L.s("Faster disk writes"), isOn: $fastFlush)
                    Toggle(L.s("Quicker wake from idle"), isOn: $wfiSpin)
                    Toggle(L.s("Superblocks (experimental)"), isOn: $superblocks)
                    Picker(L.s("Code cache"), selection: $codeCacheMB) {
                        Text(L.s("512 MB")).tag(512)
                        Text(L.s("1 GB")).tag(1024)
                        Text(L.s("1.5 GB")).tag(1536)
                    }
                    Text(L.s("A bigger code cache empties less often and takes more memory (about 1.75 times its size); Henge picks one by the Memory profile above: 512 MB where there is little room, 1.5 GB where there is plenty. Applies the next time Henge opens. If a Mac closes Henge during setup, choose a smaller one."))
                        .font(.footnote).foregroundStyle(.secondary)
                    Text(L.s("macOS draws a frame for every refresh: 30 Hz leaves the most of the emulated CPU to apps, at the cost of choppier animation; 60 Hz is smoother. Faster disk writes order them without waiting for a full sync; a sudden power loss could lose the last ones. Quicker wake keeps an idle CPU watching for work for 50 µs, at some battery cost. Superblocks let translated code run past conditional branches. Changes apply the next time a Mac starts."))
                        .font(.footnote).foregroundStyle(.secondary)
                }
                .listRowBackground(Desk.card)
                Section(L.s("Instant Resume")) {
                    Toggle(L.s("Resume where you left off"), isOn: $instantResume)
                    Text(L.s("When you leave Henge, the running Mac is saved to storage, and opening it again picks up where it was in a few seconds, even after iOS closes Henge. The save is about the size of the Mac's memory in use, compressed. The Mac pauses while Henge is in the background, so its sound stops. Experimental."))
                        .font(.footnote).foregroundStyle(.secondary)
                }
                .listRowBackground(Desk.card)
                Section(L.s("Mac Apps")) {
                    Toggle(L.s("Mac apps without macOS"), isOn: $macApps)
                    Text(L.s("Bring in a .dmg or an .app (the + button on Home) and run it inside Henge through its own translation layer, without starting a Mac. Programs without windows run today; apps with windows don't yet. Experimental."))
                        .font(.footnote).foregroundStyle(.secondary)
                }
                .listRowBackground(Desk.card)
                Section(L.s("Appearance")) {
                    Picker(L.s("Appearance"), selection: $appearance) {
                        ForEach(DeskAppearance.allCases) { Text($0.title).tag($0) }
                    }
                    .pickerStyle(.segmented)
                    Text(L.f("System follows the %@'s Light or Dark setting. Henge stays dark while a Mac is running.", Device.name))
                        .font(.footnote).foregroundStyle(.secondary)
                }
                .listRowBackground(Desk.card)
                Section(L.s("Log")) {
                    ShareLink(item: HengeLog.logFileURL) { Label(L.s("Share henge.log"), systemImage: "square.and.arrow.up") }
                }
                .listRowBackground(Desk.card)
            }
            .scrollContentBackground(.hidden)
            .background(Desk.page)
            .navigationTitle(Text(L.s("Settings")))
        }
    }
}
