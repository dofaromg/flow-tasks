import Foundation

// origin_signature: MrLiouWord
// App 與 extension 僅共用收件匣，不讓兩個程序共同覆寫標籤主檔。
enum MRLShareInbox {
    static let group = "group.com.mrliouword.app"

    static func root() throws -> URL {
        guard let container = FileManager.default.containerURL(
            forSecurityApplicationGroupIdentifier: group) else {
            throw NSError(domain: "MRLShareInbox", code: 1,
                userInfo: [NSLocalizedDescriptionKey: "未取得 MRL App Group，請檢查簽署與權限。"])
        }
        let root = container.appendingPathComponent("MRL_Inbox", isDirectory: true)
        try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
        return root
    }

    /// 在 provider callback 有效期內同步複製，目錄原子更名後才對 App 可見。
    static func receive(_ source: URL, suggestedName: String? = nil, inboxRoot: URL? = nil) throws {
        let manager = FileManager.default
        let name: String
        if let suggestedName, !suggestedName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty,
            suggestedName != ".", suggestedName != "..",
            !suggestedName.contains("/"), !suggestedName.contains("\\"),
            !suggestedName.contains("\0") {
            name = suggestedName
        } else { name = source.lastPathComponent }
        let root = try inboxRoot ?? MRLShareInbox.root()
        let id = UUID().uuidString
        let staging = root.appendingPathComponent(".staging-" + id, isDirectory: true)
        let ready = root.appendingPathComponent(id, isDirectory: true)
        try manager.createDirectory(at: staging, withIntermediateDirectories: false)
        do {
            let payload = staging.appendingPathComponent("MRL_Payload", isDirectory: true)
            try manager.createDirectory(at: payload, withIntermediateDirectories: false)
            let scoped = source.startAccessingSecurityScopedResource()
            defer { if scoped { source.stopAccessingSecurityScopedResource() } }
            let values = try source.resourceValues(forKeys: [.isRegularFileKey, .isSymbolicLinkKey])
            guard values.isRegularFile == true, values.isSymbolicLink != true else {
                throw CocoaError(.fileReadUnsupportedScheme)
            }
            var coordinationError: NSError?
            var copyError: Error?
            var storedName = name
            NSFileCoordinator().coordinate(readingItemAt: source, options: [], error: &coordinationError) { url in
                // 由目的檔案系統判定名稱能否使用，不假設固定 byte 上限。
                // 每份收件有獨立 UUID 目錄；不截斷名稱或覆寫其他收件。
                var names = [name]
                if source.lastPathComponent != name { names.append(source.lastPathComponent) }
                names.append(UUID().uuidString)
                for candidate in names {
                    let target = payload.appendingPathComponent(candidate)
                    do {
                        try manager.copyItem(at: url, to: target)
                        storedName = candidate
                        copyError = nil
                        break
                    } catch {
                        copyError = error
                        // 只清除此輪未完成的 staging 副本，來源始終保留。
                        if manager.fileExists(atPath: target.path) {
                            do { try manager.removeItem(at: target) }
                            catch { copyError = error; break }
                        }
                    }
                }
            }
            if let coordinationError { throw coordinationError }
            if let copyError { throw copyError }
            let provenance: [String: String] = ["origin_signature": "MrLiouWord",
                "source_record": id, "original_name": name, "stored_name": storedName,
                "received_at": ISO8601DateFormatter().string(from: Date()),
                "mode": "Files_share_copy", "native_tags": "not_imported"]
            try JSONSerialization.data(withJSONObject: provenance, options: [.sortedKeys])
                .write(to: staging.appendingPathComponent(".MRL_source.json"), options: .atomic)
            try manager.moveItem(at: staging, to: ready)
        } catch {
            try? manager.removeItem(at: staging)
            throw error
        }
    }
}
