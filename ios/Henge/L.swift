import Foundation

/// User-visible strings. Static SwiftUI literals already localize through the
/// `Localizable.strings` files in `Henge/Resources`; the dynamic ones (interpolations,
/// computed titles, `LabeledContent` values and the error messages the engine raises) go
/// through this helper, so they resolve from the same table.
enum L {
    static func s(_ key: String, _ comment: String = "") -> String {
        NSLocalizedString(key, comment: comment)
    }

    static func f(_ key: String, _ args: CVarArg..., comment: String = "") -> String {
        String(format: NSLocalizedString(key, comment: comment), arguments: args)
    }
}
