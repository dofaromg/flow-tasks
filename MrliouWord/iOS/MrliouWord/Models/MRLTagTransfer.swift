import Foundation

// origin_signature: MrLiouWord
// 可攜封包不包含 bookmark、裝置路徑或存取權限。
struct MRLTagTransfer: Codable, Equatable {
    static let maximumBytes = 16 * 1024 * 1024
    var version = 1
    var originSignature = "MrLiouWord"
    var documents: [Entry]

    struct Entry: Codable, Equatable {
        let name: String
        let sha256: String
        let tags: Set<String>
    }

    enum ValidationError: Error { case invalidPacket }

    /// 先完整驗證，拒絕未知版本、來源標記、非法雜湊與過大清單。
    func validate() throws {
        guard version == 1, originSignature == "MrLiouWord", documents.count <= 10000,
            documents.allSatisfy({ entry in
                !entry.name.isEmpty && entry.name.utf8.count <= 1024 &&
                !entry.name.contains("/") && !entry.name.contains("\\") &&
                entry.sha256.count == 64 && entry.sha256.allSatisfy({ "0123456789abcdef".contains($0) }) &&
                entry.tags.count <= 1000 && entry.tags.allSatisfy({
                    !$0.isEmpty && $0 == $0.trimmingCharacters(in: .whitespacesAndNewlines) && $0.utf8.count <= 1024
                })
            }) else { throw ValidationError.invalidPacket }
    }

    func encoded() throws -> Data {
        try validate()
        let data = try JSONEncoder().encode(self)
        guard data.count <= Self.maximumBytes else { throw ValidationError.invalidPacket }
        return data
    }

    /// 同名且內容雜湊相同才連結；以聯集保留所有舊標籤，不相信外部 UUID。
    func merging(into archive: MRLTagArchive, fingerprints: [UUID: String]) throws -> MRLTagArchive {
        try validate()
        var candidate = archive
        let byName = Dictionary(grouping: documents, by: \.name)
        for i in candidate.documents.indices {
            let document = candidate.documents[i]
            for entry in byName[document.name] ?? [] where
                fingerprints[document.id] == entry.sha256 {
                for tag in entry.tags.sorted() { candidate.addTag(tag) }
                let merged = candidate.documents[i].tags.union(entry.tags)
                guard merged.count <= 1000 else { throw ValidationError.invalidPacket }
                candidate.documents[i].tags = merged
            }
        }
        return candidate
    }
}
