#!/usr/bin/env python3
"""Third pass: the remaining user-visible returns and error strings."""
import sys

PAIRS = {
'ios/Henge/InstallView.swift': [
 ('Text(Device.chipTooOld ? Device.chipTooOldText : jitReady ? "Keep Henge open and the \\(Device.name) plugged in. Needs about \\(ByteText.string(UInt64(Installer.spaceNeeded(release)))) free."\n                                : JITBootstrap.lastFailure ?? jit.automaticDescription)',
  'Text(Device.chipTooOld ? Device.chipTooOldText : jitReady ? L.f("Keep Henge open and the %@ plugged in. Needs about %@ free.", String(describing: Device.name), String(describing: ByteText.string(UInt64(Installer.spaceNeeded(release)))))\n                                : (JITBootstrap.lastFailure.map(L.s) ?? jit.automaticDescription))'),
],
'ios/Henge/JIT/JITBuiltIn.swift': [
 ('return "Built-in JIT is available only on a physical device."',
  'return L.s("Built-in JIT is available only on a physical device.")'),
 ('return "Built-in JIT needs iOS 26 or later. Use StikDebug instead."',
  'return L.s("Built-in JIT needs iOS 26 or later. Use StikDebug instead.")'),
 ('return "Built-in JIT is unavailable inside LiveContainer. Use StikDebug instead."',
  'return L.s("Built-in JIT is unavailable inside LiveContainer. Use StikDebug instead.")'),
],
'ios/Henge/Installer.swift': [
 ('case 0: return "Finding the Mac"', 'case 0: return L.s("Finding the Mac")'),
 ('case 1: return "Starting the installer"', 'case 1: return L.s("Starting the installer")'),
 ('case 2: return "Writing macOS"', 'case 2: return L.s("Writing macOS")'),
 ('case 3: return "Checking macOS"', 'case 3: return L.s("Checking macOS")'),
 ('case 4: return "Installing firmware"', 'case 4: return L.s("Installing firmware")'),
 ('case 6, 7: return "Installing system files"', 'case 6, 7: return L.s("Installing system files")'),
 ('default: return "Installing"', 'default: return L.s("Installing")'),
],
'ios/Henge/SessionView.swift': [
 ('case 3: return "Finishing shutdown…"', 'case 3: return L.s("Finishing shutdown…")'),
 ('default: return "Stopped (\\(String(cString: henge_vm_exit_reason())))"',
  'default: return L.f("Stopped (%@)", String(describing: String(cString: henge_vm_exit_reason())))'),
],
'ios/Henge/StoppedMacView.swift': [
 ('case Int32(HENGE_VM_OUTCOME_SHUTDOWN.rawValue): return "Mac shut down"',
  'case Int32(HENGE_VM_OUTCOME_SHUTDOWN.rawValue): return L.s("Mac shut down")'),
 ('case Int32(HENGE_VM_OUTCOME_RESTART.rawValue): return "Mac requested a restart"',
  'case Int32(HENGE_VM_OUTCOME_RESTART.rawValue): return L.s("Mac requested a restart")'),
 ('case Int32(HENGE_VM_OUTCOME_HOST_STOP.rawValue): return "Mac stopped"',
  'case Int32(HENGE_VM_OUTCOME_HOST_STOP.rawValue): return L.s("Mac stopped")'),
 ('default: return "Mac stopped unexpectedly"', 'default: return L.s("Mac stopped unexpectedly")'),
 ('case Int32(HENGE_VM_OUTCOME_RESTART.rawValue): return "The Mac is ready to start again."',
  'case Int32(HENGE_VM_OUTCOME_RESTART.rawValue): return L.s("The Mac is ready to start again.")'),
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
                print('MISS %s :: %s' % (path, old[:100]))
                missing += 1
        open(path, 'w', encoding='utf-8').write(src)
    print('missing:', missing)
