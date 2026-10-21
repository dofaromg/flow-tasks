import Foundation

enum L10n {
    static func t(_ key: String, _ args: CVarArg...) -> String {
        let format = NSLocalizedString(key, tableName: nil, bundle: .main, value: key, comment: "")
        if args.isEmpty { return format }
        return String(format: format, locale: Locale.current, arguments: args)
    }
}
