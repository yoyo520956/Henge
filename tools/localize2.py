#!/usr/bin/env python3
"""Second pass: wrap the remaining user-visible literals (helper calls, ternaries,
computed properties) in L.s / L.f."""
import sys

PAIRS = {
'ios/Henge/Theme.swift': [
 ('case .system: return "System"', 'case .system: return L.s("System")'),
 ('case .light: return "Light"', 'case .light: return L.s("Light")'),
 ('case .dark: return "Dark"', 'case .dark: return L.s("Dark")'),
],
'ios/Henge/MacApps.swift': [
 ('.navigationTitle("Mac Apps")', '.navigationTitle(Text(L.s("Mac Apps")))'),
 ('DeskHeading("About")', 'DeskHeading(L.s("About"))'),
 ('DeskHeading("Output")', 'DeskHeading(L.s("Output"))'),
 ('Button(running ? "Running…" : "Run")', 'Button(running ? L.s("Running…") : L.s("Run"))'),
 ('Text(output.isEmpty ? "(nothing printed)" : output)', 'Text(output.isEmpty ? L.s("(nothing printed)") : output)'),
],
'ios/Henge/InstallView.swift': [
 ('.navigationTitle(installer.busy ? "Installing" : "Install macOS")',
  '.navigationTitle(Text(installer.busy ? L.s("Installing") : L.s("Install macOS")))'),
 ('DeskHeading("Version")', 'DeskHeading(L.s("Version"))'),
 ('DeskHeading("New Mac")', 'DeskHeading(L.s("New Mac"))'),
 ('DeskHeading("Steps")', 'DeskHeading(L.s("Steps"))'),
 ('DeskHeading("Log")', 'DeskHeading(L.s("Log"))'),
 ('Button(Installer.haveImage(release) ? "Install" : "Download and Install")',
  'Button(Installer.haveImage(release) ? L.s("Install") : L.s("Download and Install"))'),
 ('private static let stages = ["Download", "Start installer", "Write macOS", "Check macOS", "Finish"]',
  'private static var stages: [String] { [L.s("Download"), L.s("Start installer"), L.s("Write macOS"), L.s("Check macOS"), L.s("Finish")] }'),
 ('Button(details ? "Hide details" : "Show details")', 'Button(details ? L.s("Hide details") : L.s("Show details"))'),
 ('Text(timeLeft ?? "Step \\(stage + 1) of \\(Self.stages.count)")',
  'Text(timeLeft ?? L.f("Step %@ of %@", String(describing: stage + 1), String(describing: Self.stages.count)))'),
],
'ios/Henge/MacSettingsView.swift': [
 ('DeskHeading("Name")', 'DeskHeading(L.s("Name"))'),
 ('DeskHeading("Memory")', 'DeskHeading(L.s("Memory"))'),
 ('DeskHeading("Processors")', 'DeskHeading(L.s("Processors"))'),
 ('DeskHeading("Screen")', 'DeskHeading(L.s("Screen"))'),
 ('DeskHeading("Storage")', 'DeskHeading(L.s("Storage"))'),
 ('DeskHeading("Manage")', 'DeskHeading(L.s("Manage"))'),
 ('Text(Entitlements.increasedMemory ? "Outside the app\'s limit once JIT is on" : "Used from free storage if needed")',
  'Text(Entitlements.increasedMemory ? L.s("Outside the app\'s limit once JIT is on") : L.s("Used from free storage if needed"))'),
 ('row("Export", symbol:', 'row(L.s("Export"), symbol:'),
 ('row("Delete this Mac", symbol:', 'row(L.s("Delete this Mac"), symbol:'),
],
'ios/Henge/HomeView.swift': [
 ('.navigationTitle("Henge")', '.navigationTitle(Text(L.s("Henge")))'),
 ('DeskHeading("Other Macs")', 'DeskHeading(L.s("Other Macs"))'),
 ('guard let lastUsed else { return "Never" }', 'guard let lastUsed else { return L.s("Never") }'),
 ('if Calendar.current.isDateInToday(lastUsed) { return "Today" }', 'if Calendar.current.isDateInToday(lastUsed) { return L.s("Today") }'),
 ('if Calendar.current.isDateInYesterday(lastUsed) { return "Yesterday" }', 'if Calendar.current.isDateInYesterday(lastUsed) { return L.s("Yesterday") }'),
 ('Text(jitReady ? "JIT on" : "JIT off")', 'Text(jitReady ? L.s("JIT on") : L.s("JIT off"))'),
],
'ios/Henge/SettingsView.swift': [
 ('return "Tap to click once. Tap then hold to begin dragging. Quickly tap with two fingers to right-click."',
  'return L.s("Tap to click once. Tap then hold to begin dragging. Quickly tap with two fingers to right-click.")'),
 ('return "Delay hold waits to see if you\'re holding or just clicking the volume button, which results in all clicks being ~0.5s long."',
  'return L.s("Delay hold waits to see if you\'re holding or just clicking the volume button, which results in all clicks being ~0.5s long.")'),
 ('return "Tap then drag waits to see if you\'re holding or just clicking the volume button, but it unconditionally sends a single click regardless of whether you tap or hold, which results in shorter clicks at the cost of sending a click before holding."',
  'return L.s("Tap then drag waits to see if you\'re holding or just clicking the volume button, but it unconditionally sends a single click regardless of whether you tap or hold, which results in shorter clicks at the cost of sending a click before holding.")'),
 ('return "Activates the camera in order to intercept volume keys properly. This causes the volume keys to behave in the same way a mouse\'s buttons do, but it causes higher temperatures, as the camera is always on."',
  'return L.s("Activates the camera in order to intercept volume keys properly. This causes the volume keys to behave in the same way a mouse\'s buttons do, but it causes higher temperatures, as the camera is always on.")'),
 ('Text(jit.method == .automatic ? jit.automaticDescription : "Henge uses \\(jit.method.title).")',
  'Text(jit.method == .automatic ? jit.automaticDescription : L.f("Henge uses %@.", String(describing: jit.method.title)))'),
 ('.navigationTitle("Settings")', '.navigationTitle(Text(L.s("Settings")))'),
],
'ios/Henge/BootROM.swift': [
 ('case .download(let why): return "Henge couldn\'t get the Mac\'s boot ROM from Apple (\\(why)). Check the connection and try again."',
  'case .download(let why): return L.f("Henge couldn\'t get the Mac\'s boot ROM from Apple (%@). Check the connection and try again.", String(describing: why))'),
 ('case .damaged: return "The Mac\'s boot ROM from Apple wasn\'t what Henge expected, so it wasn\'t used. Check the connection and try again, or look for an update to Henge."',
  'case .damaged: return L.s("The Mac\'s boot ROM from Apple wasn\'t what Henge expected, so it wasn\'t used. Check the connection and try again, or look for an update to Henge.")'),
],
'ios/Henge/Hardware.swift': [
 ('if gb < 4 { return "macOS has little room under 4 GB, so it can be very slow." }',
  'if gb < 4 { return L.s("macOS has little room under 4 GB, so it can be very slow.") }'),
 ('if gb > suggestedRAMGB { return "More than \\(suggestedRAMGB) GB is a lot for this \\(name): iOS may close Henge when macOS gets busy." }',
  'if gb > suggestedRAMGB { return L.f("More than %@ GB is a lot for this %@: iOS may close Henge when macOS gets busy.", String(describing: suggestedRAMGB), String(describing: name)) }'),
],
'ios/Henge/JIT/JITSetup.swift': [
 ('case .automatic: return "Automatic"', 'case .automatic: return L.s("Automatic")'),
 ('case .stikDebug: return "StikDebug"', 'case .stikDebug: return L.s("StikDebug")'),
 ('case .trollStore: return "TrollStore"', 'case .trollStore: return L.s("TrollStore")'),
 ('case .jailbreak: return "Jailbreak (Dopamine)"', 'case .jailbreak: return L.s("Jailbreak (Dopamine)")'),
 ('case .builtIn: return "Built-in StikJIT"', 'case .builtIn: return L.s("Built-in StikJIT")'),
 ('case .stikDebug: return "StikDebug is installed, so Henge will open it."',
  'case .stikDebug: return L.s("StikDebug is installed, so Henge will open it.")'),
 ('case .trollStore: return "TrollStore is installed, so Henge will ask it to enable JIT."',
  'case .trollStore: return L.s("TrollStore is installed, so Henge will ask it to enable JIT.")'),
 ('case .jailbreak: return "This device is jailbroken, so JIT comes from the jailbreak\'s Allow JIT in Apps setting."',
  'case .jailbreak: return L.s("This device is jailbroken, so JIT comes from the jailbreak\'s Allow JIT in Apps setting.")'),
 ('? "Henge will use its paired built-in helper."', '? L.s("Henge will use its paired built-in helper.")'),
 (': "StikDebug, TrollStore and a jailbreak were not found, so Henge will use its built-in helper."',
  ': L.s("StikDebug, TrollStore and a jailbreak were not found, so Henge will use its built-in helper.")'),
],
'ios/Henge/JIT/JITSetupView.swift': [
 ('Text(jit.status ?? "Working…")', 'Text(jit.status ?? L.s("Working…"))'),
 ('Button(OnDevicePairing.isSupported ? "Pair again" : "Import a new pairing file")',
  'Button(OnDevicePairing.isSupported ? L.s("Pair again") : L.s("Import a new pairing file"))'),
],
'ios/Henge/JIT/JITPairing.swift': [
 ('task.updateTitle("Pairing code \\(pin)", subtitle: "Enter it on this \\(Self.deviceKind) to pair with Henge")',
  'task.updateTitle(L.f("Pairing code %@", String(describing: pin)), subtitle: L.f("Enter it on this %@ to pair with Henge", String(describing: Self.deviceKind)))'),
],
'ios/Henge/SessionView.swift': [
 ('tool("eye.slash", "Hide controls")', 'tool("eye.slash", L.s("Hide controls"))'),
 ('tool("keyboard", "Keyboard")', 'tool("keyboard", L.s("Keyboard"))'),
 ('tool("plus.magnifyingglass", "Zoom in")', 'tool("plus.magnifyingglass", L.s("Zoom in"))'),
 ('tool("info.circle", "Details")', 'tool("info.circle", L.s("Details"))'),
 ('tool("power", "Shut down", tint: Desk.bad)', 'tool("power", L.s("Shut down"), tint: Desk.bad)'),
 ('tool("eye.slash", "Hide controls", tint: .white)', 'tool("eye.slash", L.s("Hide controls"), tint: .white)'),
 ('tool("keyboard", "Keyboard", tint: .white)', 'tool("keyboard", L.s("Keyboard"), tint: .white)'),
 ('tool("info.circle", "Details", tint: .white)', 'tool("info.circle", L.s("Details"), tint: .white)'),
 ('zoomed ? "Zoom out" : "Zoom in"', 'zoomed ? L.s("Zoom out") : L.s("Zoom in")'),
 ('hint("Drag", "to move")', 'hint(L.s("Drag"), L.s("to move"))'),
 ('hint("Tap", "to click")', 'hint(L.s("Tap"), L.s("to click"))'),
 ('hint("Hold, then drag", "to grab")', 'hint(L.s("Hold, then drag"), L.s("to grab"))'),
 ('hint("Two fingers", "to scroll")', 'hint(L.s("Two fingers"), L.s("to scroll"))'),
 ('MouseButton(title: "Click", button: 0)', 'MouseButton(title: L.s("Click"), button: 0)'),
 ('MouseButton(title: "Right-click", button: 1)', 'MouseButton(title: L.s("Right-click"), button: 1)'),
 ('.navigationTitle("Details")', '.navigationTitle(Text(L.s("Details")))'),
 ('case .nominal: return "Normal"', 'case .nominal: return L.s("Normal")'),
 ('case .fair: return "Warm"', 'case .fair: return L.s("Warm")'),
 ('case .serious: return "Hot — performance reduced"', 'case .serious: return L.s("Hot — performance reduced")'),
 ('case .critical: return "Critical"', 'case .critical: return L.s("Critical")'),
 ('@unknown default: return "Unknown"', '@unknown default: return L.s("Unknown")'),
],
}

if __name__ == '__main__':
    missing = 0
    for path, pairs in PAIRS.items():
        src = open(path, encoding='utf-8').read()
        for old, new in pairs:
            if old in src:
                src = src.replace(old, new)
            else:
                print('MISS %s :: %s' % (path, old[:80]))
                missing += 1
        open(path, 'w', encoding='utf-8').write(src)
    print('missing:', missing)
