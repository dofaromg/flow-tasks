import Foundation
import Combine
import CryptoKit

// origin_signature: MrLiouWord
@MainActor
final class MRLTagStore: ObservableObject {
    @Published private(set) var archive = MRLTagArchive()
    @Published var errorMessage: String?
    private var writable = true
    private let location: URL

    init(location: URL? = nil) {
        self.location = location ?? FileManager.default.urls(
            for: .applicationSupportDirectory, in: .userDomainMask
        )[0].appendingPathComponent("MRL_TagArchive.json")
        do {
            if FileManager.default.fileExists(atPath: self.location.path) {
                let loaded = try JSONDecoder().decode(MRLTagArchive.self,
                    from: Data(contentsOf: self.location))
                guard loaded.version == 1, loaded.originSignature == "MrLiouWord" else { throw StoreError.unsupportedVersion }
                guard Set(loaded.documents.map(\.id)).count == loaded.documents.count,
                    Set(loaded.catalog).count == loaded.catalog.count else { throw StoreError.unsupportedVersion }
                archive = loaded
            }
        } catch {
            writable = false
            errorMessage = "既有標籤資料無法讀取，已停止寫入保留原件：\(error.localizedDescription)"
        }
    }

    @discardableResult
    private func commit(_ candidate: MRLTagArchive) -> Bool {
        guard writable else {
            errorMessage = "原有標籤資料無法讀取，已停止寫入；請先保留並修復原件。"
            return false
        }
        do {
            try FileManager.default.createDirectory(
                at: location.deletingLastPathComponent(), withIntermediateDirectories: true)
            let data = try JSONEncoder().encode(candidate)
            try data.write(to: location, options: .atomic)
            archive = candidate
            errorMessage = nil
            return true
        } catch {
            errorMessage = "標籤尚未儲存：\(error.localizedDescription)"
            return false
        }
    }

    func addTag(_ name: String) {
        var candidate = archive
        guard candidate.addTag(name) else {
            errorMessage = "標籤不可空白或超過 1024 UTF-8 位元組。"
            return
        }
        commit(candidate)
    }

    @discardableResult
    func register(_ urls: [URL], sourceRecord: String? = nil) -> Bool {
        var candidate = archive
        do {
            var registered = Set<URL>()
            for i in candidate.documents.indices {
                var stale = false
                if let resolved = try? URL(resolvingBookmarkData: candidate.documents[i].bookmark,
                    options: [], relativeTo: nil, bookmarkDataIsStale: &stale) {
                    registered.insert(resolved.standardizedFileURL)
                    if stale {
                        let scoped = resolved.startAccessingSecurityScopedResource()
                        defer { if scoped { resolved.stopAccessingSecurityScopedResource() } }
                        candidate.documents[i].bookmark = try resolved.bookmarkData(options: .minimalBookmark,
                            includingResourceValuesForKeys: nil, relativeTo: nil)
                    }
                }
            }
            for url in urls {
                let scoped = url.startAccessingSecurityScopedResource()
                defer { if scoped { url.stopAccessingSecurityScopedResource() } }
                guard try url.resourceValues(forKeys: [.isRegularFileKey]).isRegularFile == true else {
                    throw CocoaError(.fileReadUnsupportedScheme)
                }
                guard !registered.contains(url.standardizedFileURL) else { continue }
                let bookmark = try url.bookmarkData(options: .minimalBookmark,
                    includingResourceValuesForKeys: nil, relativeTo: nil)
                candidate.documents.append(MRLTaggedDocument(
                    id: UUID(), name: url.lastPathComponent, bookmark: bookmark, tags: [], sourceRecord: sourceRecord))
                registered.insert(url.standardizedFileURL)
            }
            return commit(candidate)
        } catch {
            errorMessage = "檔案尚未加入：\(error.localizedDescription)"
            return false
        }
    }

    /// 收件匣成功登錄後才移除；失敗保留副本，重新啟動可重試。
    func receiveSharedFiles(inboxRoot: URL? = nil, importsRoot: URL? = nil) {
        do {
            let manager = FileManager.default
            let inbox = try inboxRoot ?? MRLShareInbox.root()
            let imports = importsRoot ?? manager.urls(for: .documentDirectory, in: .userDomainMask)[0]
                .appendingPathComponent("MRL_匯入", isDirectory: true)
            try manager.createDirectory(at: imports, withIntermediateDirectories: true)
            var failures: [String] = []
            for folder in try manager.contentsOfDirectory(at: inbox,
                includingPropertiesForKeys: nil, options: [.skipsHiddenFiles]) {
                guard UUID(uuidString: folder.lastPathComponent) != nil else { continue }
                do {
                    let destination = imports.appendingPathComponent(folder.lastPathComponent, isDirectory: true)
                    if !manager.fileExists(atPath: destination.path) {
                        let staging = imports.appendingPathComponent(".staging-" + UUID().uuidString)
                        do {
                            try manager.copyItem(at: folder, to: staging)
                            try manager.moveItem(at: staging, to: destination)
                        } catch {
                            try? manager.removeItem(at: staging)
                            throw error
                        }
                    }
                    // 逐件修復缺少的副本；衝突保留兩側原件，禁止靜默覆寫。
                    let incoming = folder.appendingPathComponent("MRL_Payload")
                    let payload = destination.appendingPathComponent("MRL_Payload")
                    try manager.createDirectory(at: payload, withIntermediateDirectories: true)
                    for source in try manager.contentsOfDirectory(at: incoming, includingPropertiesForKeys: nil) {
                        let target = payload.appendingPathComponent(source.lastPathComponent)
                        if !manager.fileExists(atPath: target.path) { try manager.copyItem(at: source, to: target) }
                        guard try Self.digest(source) == Self.digest(target) else {
                            throw CocoaError(.fileWriteFileExists)
                        }
                    }
                    let sourceRecord = folder.appendingPathComponent(".MRL_source.json")
                    let savedRecord = destination.appendingPathComponent(".MRL_source.json")
                    if !manager.fileExists(atPath: savedRecord.path) {
                        try manager.copyItem(at: sourceRecord, to: savedRecord)
                    }
                    guard try Self.digest(sourceRecord) == Self.digest(savedRecord) else {
                        throw CocoaError(.fileWriteFileExists)
                    }
                    let files = try manager.contentsOfDirectory(at: incoming, includingPropertiesForKeys: nil)
                        .map { payload.appendingPathComponent($0.lastPathComponent) }
                    guard !files.isEmpty, register(files, sourceRecord: folder.lastPathComponent) else {
                        throw CocoaError(.fileWriteUnknown)
                    }
                    try manager.removeItem(at: folder)
                } catch {
                    failures.append("\(folder.lastPathComponent)：\(error.localizedDescription)")
                }
            }
            if !failures.isEmpty { errorMessage = "分享收件匣保留待重試：" + failures.joined(separator: "；") }
        } catch { errorMessage = "分享收件匣尚未完成：\(error.localizedDescription)" }
    }

    /// 只輸出可攜標籤，不洩漏 bookmark 或本機路徑。
    func transferData(for ids: Set<UUID>) throws -> Data {
        let entries = try archive.documents.filter { ids.contains($0.id) }.map { document in
            try withDocument(document) { url in
                MRLTagTransfer.Entry(name: document.name, sha256: try Self.digest(url), tags: document.tags)
            }
        }
        let packet = MRLTagTransfer(documents: entries)
        try packet.validate()
        return try packet.encoded()
    }

    /// 匯入前完整驗證；只對使用者選取的 MRL 文件比對內容，不以名稱單獨套用。
    func importTransfer(_ url: URL, to ids: Set<UUID>) -> Int? {
        do {
            let scoped = url.startAccessingSecurityScopedResource()
            defer { if scoped { url.stopAccessingSecurityScopedResource() } }
            let data = try Self.coordinated(url) { coordinated in
                let handle = try FileHandle(forReadingFrom: coordinated)
                defer { try? handle.close() }
                let maximum = MRLTagTransfer.maximumBytes
                let bytes = try handle.read(upToCount: maximum + 1) ?? Data()
                guard bytes.count <= maximum else { throw MRLTagTransfer.ValidationError.invalidPacket }
                return bytes
            }
            let packet = try JSONDecoder().decode(MRLTagTransfer.self, from: data)
            try packet.validate()
            var fingerprints: [UUID: String] = [:]
            for document in archive.documents where ids.contains(document.id) {
                fingerprints[document.id] = try withDocument(document) { try Self.digest($0) }
            }
            let matches = archive.documents.filter { document in
                packet.documents.contains { $0.name == document.name && $0.sha256 == fingerprints[document.id] }
            }.count
            let candidate = try packet.merging(into: archive, fingerprints: fingerprints)
            return commit(candidate) ? matches : nil
        } catch {
            errorMessage = "標籤封包尚未匯入：\(error.localizedDescription)"
            return nil
        }
    }

    /// 分享副本與標籤封包，完整準備成功才顯示分享面板。
    func exportFiles(_ ids: Set<UUID>) throws -> (directory: URL, files: [URL]) {
        let manager = FileManager.default
        let directory = manager.temporaryDirectory.appendingPathComponent("MRL_" + UUID().uuidString)
        try manager.createDirectory(at: directory, withIntermediateDirectories: false)
        do {
            var files: [URL] = []
            for document in archive.documents where ids.contains(document.id) {
                let child = directory.appendingPathComponent(document.id.uuidString, isDirectory: true)
                try manager.createDirectory(at: child, withIntermediateDirectories: false)
                let copy = child.appendingPathComponent(document.name)
                try withDocument(document) { try manager.copyItem(at: $0, to: copy) }
                files.append(copy)
            }
            let packet = directory.appendingPathComponent("MRL_標籤.json")
            // 從實際分享副本計算，避免原件在兩次讀取間改變造成配對錯誤。
            let selected = archive.documents.filter { ids.contains($0.id) }
            let entries = try zip(selected, files).map { document, file in
                MRLTagTransfer.Entry(name: document.name, sha256: try Self.digest(file), tags: document.tags)
            }
            let transfer = MRLTagTransfer(documents: entries)
            try transfer.validate()
            try transfer.encoded().write(to: packet, options: .atomic)
            files.append(packet)
            return (directory, files)
        } catch {
            try? manager.removeItem(at: directory)
            throw error
        }
    }

    private func withDocument<T>(_ document: MRLTaggedDocument, body: (URL) throws -> T) throws -> T {
        var stale = false
        let url = try URL(resolvingBookmarkData: document.bookmark, options: [],
            relativeTo: nil, bookmarkDataIsStale: &stale)
        let scoped = url.startAccessingSecurityScopedResource()
        defer { if scoped { url.stopAccessingSecurityScopedResource() } }
        if stale, let index = archive.documents.firstIndex(where: { $0.id == document.id }) {
            var candidate = archive
            candidate.documents[index].bookmark = try url.bookmarkData(options: .minimalBookmark,
                includingResourceValuesForKeys: nil, relativeTo: nil)
            guard commit(candidate) else { throw CocoaError(.fileWriteUnknown) }
        }
        return try Self.coordinated(url, body: body)
    }

    private static func coordinated<T>(_ url: URL, body: (URL) throws -> T) throws -> T {
        var coordinationError: NSError?
        var result: Result<T, Error>?
        NSFileCoordinator().coordinate(readingItemAt: url, options: [], error: &coordinationError) { coordinated in
            result = Result { try body(coordinated) }
        }
        if let coordinationError { throw coordinationError }
        guard let result else { throw CocoaError(.fileReadUnknown) }
        return try result.get()
    }

    private static func digest(_ url: URL) throws -> String {
        let handle = try FileHandle(forReadingFrom: url)
        defer { try? handle.close() }
        var hash = SHA256()
        while let data = try handle.read(upToCount: 1024 * 1024), !data.isEmpty { hash.update(data: data) }
        return hash.finalize().map { String(format: "%02x", $0) }.joined()
    }

    func apply(tags: Set<String>, to ids: Set<UUID>) -> Bool {
        guard !tags.isEmpty, !ids.isEmpty else { return false }
        var candidate = archive
        guard candidate.apply(tags: tags, to: ids) else {
            errorMessage = "每份文件最多保留 1000 個標籤；本次未寫入。"
            return false
        }
        return commit(candidate)
    }

    private enum StoreError: LocalizedError {
        case unsupportedVersion
        var errorDescription: String? { "不支援此資料版本" }
    }
}
