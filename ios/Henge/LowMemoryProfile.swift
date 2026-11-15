import Foundation

/// How Henge should spend this device's memory, chosen by the device it is running on and
/// overridable in Settings. Henge picks it from physical RAM and the memory limit iOS gave
/// the app at launch — not from physical RAM alone, because the app's own limit is the number
/// jetsam kills on, and it varies with the increased-memory-limit entitlement.
enum LowMemoryProfile {
    /// The user's choice in Settings. "Auto" (the default) is what this type computes; the
    /// others are fixed, so a user who picked "Performance" on a tight phone is not second-guessed.
    enum Mode: Int {
        case auto, low, balanced, performance
        var key: String {
            switch self {
            case .auto: return "Auto"
            case .low: return "Low memory"
            case .balanced: return "Balanced"
            case .performance: return "Performance"
            }
        }
    }

    static let modeKey = "henge.perf.memoryProfile"

    static var mode: Mode { Mode(rawValue: UserDefaults.standard.integer(forKey: modeKey)) ?? .auto }

    /// What jetsam kills on: how much this process may still allocate at launch, before the
    /// JIT region takes its share.
    static var limitMB: Int { Int(Entitlements.memoryLimitAtLaunch >> 20) }

    /// Auto: low when the device is a 4 GB one, or when iOS's limit for this app is under
    /// 3 GB — the point at which a 1 GB code cache and its records left a 2 GB Mac no room
    /// in Setup (#70). Balanced otherwise, and performance only where the limit has real headroom.
    static var active: Mode {
        switch mode {
        case .low, .balanced, .performance:
            return mode
        case .auto:
            if Device.lowMemory || limitMB < 3_000 { return .low }
            if limitMB >= 5_500 { return .performance }
            return .balanced
        }
    }

    /// The code cache the low-memory point picks: 512 MB (about 0.9 GB with its records,
    /// instead of 1.75), and what "performance" spends where the limit has room for it.
    static var preferredCodeCacheMB: Int {
        switch active {
        case .low: return 512
        case .balanced: return 1024
        case .performance: return 1536
        case .auto: return 1024
        }
    }

    /// 30 Hz leaves the most of the emulated CPU to the Mac, at the cost of choppier
    /// animation — the right trade for a phone that is already short of both.
    static var preferredRefreshRate: Int { active == .low ? 30 : 60 }

    /// The temporary Mac the installer boots to run macOS's own restore: 2 GB on a
    /// low-memory device, 4 GB where the phone can hold it.
    static var restoreCapMB: Int { active == .low ? 2048 : 4096 }
}
