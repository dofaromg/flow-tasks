import Foundation
import Combine

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
                guard loaded.version == 1 else { throw StoreError.unsupportedVersion }
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
            return true
        } catch {
            errorMessage = "標籤尚未儲存：\(error.localizedDescription)"
            return false
        }
    }

    func addTag(_ name: String) {
        var candidate = archive
        candidate.addTag(name)
        commit(candidate)
    }

    func register(_ urls: [URL]) {
        var candidate = archive
        do {
            for url in urls {
                let scoped = url.startAccessingSecurityScopedResource()
                defer { if scoped { url.stopAccessingSecurityScopedResource() } }
                var alreadyRegistered = false
                for existing in candidate.documents {
                    var stale = false
                    if let resolved = try? URL(resolvingBookmarkData: existing.bookmark,
                        options: [], relativeTo: nil, bookmarkDataIsStale: &stale),
                        resolved.standardizedFileURL == url.standardizedFileURL {
                        alreadyRegistered = true
                        break
                    }
                }
                guard !alreadyRegistered else { continue }
                let bookmark = try url.bookmarkData(options: .minimalBookmark,
                    includingResourceValuesForKeys: nil, relativeTo: nil)
                candidate.documents.append(MRLTaggedDocument(
                    id: UUID(), name: url.lastPathComponent, bookmark: bookmark, tags: []))
            }
            commit(candidate)
        } catch {
            errorMessage = "檔案尚未加入：\(error.localizedDescription)"
        }
    }

    func apply(tags: Set<String>, to ids: Set<UUID>) -> Bool {
        guard !tags.isEmpty, !ids.isEmpty else { return false }
        var candidate = archive
        candidate.apply(tags: tags, to: ids)
        return commit(candidate)
    }

    private enum StoreError: LocalizedError {
        case unsupportedVersion
        var errorDescription: String? { "不支援此資料版本" }
    }
}
