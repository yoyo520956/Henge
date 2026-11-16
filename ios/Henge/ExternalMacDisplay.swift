import SwiftUI

/// The accessory only presents the existing Mac's pixels. It never owns or
/// starts a VM, and hardware input continues through the phone's SessionView.
struct ExternalMacDisplay: View {
    let presentation: MacPresentation
    /// The id this display's view connects to the router under; a display scene passes its own.
    var surface = UUID()

    var body: some View {
        GeometryReader { geometry in
            let aspect = presentation.aspect
            let width = min(geometry.size.width, geometry.size.height * aspect)
            BootDisplay(display: presentation.display, role: .external, surface: surface)
                .frame(width: width, height: width / aspect)
                .frame(maxWidth: .infinity, maxHeight: .infinity)
        }
        .background(.black)
        .ignoresSafeArea()
        .allowsHitTesting(false)
        .preferredColorScheme(.dark)
    }
}

/// Puts the session's Mac on an external display. iOS 27 delivers that scene only to this
/// accessory; earlier iOS connects it to ExternalDisplaySceneDelegate (LegacyExternalDisplay),
/// which is told about the session either way and acts only where iOS gives it scenes.
struct ExternalMacDisplayModifier: ViewModifier {
    let presentation: MacPresentation

    func body(content: Content) -> some View {
        // sceneAccessory and ExternalNonInteractiveAccessory ship only in the
        // iOS 27 SDK. This build uses Xcode 16.4 / iOS 18.5 SDK, where those
        // symbols do not exist; #available guards runtime, not symbol
        // availability, so that branch cannot compile here. The legacy
        // external-display scene delegate covers iOS 17-26.
        content
            .onAppear { LegacyExternalDisplay.shared.begin(presentation) }
            .onDisappear { LegacyExternalDisplay.shared.end(presentation) }
    }
}
