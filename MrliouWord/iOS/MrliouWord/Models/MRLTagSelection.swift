import Foundation

// origin_signature: MrLiouWord
// 選取範圍永遠是完整資料集合，與畫面捲動位置無關。
struct MRLTagSelection<ID: Hashable> {
    let all: Set<ID>
    private(set) var selected: Set<ID>

    init(all: [ID], selected: Set<ID> = []) {
        self.all = Set(all)
        self.selected = selected.intersection(self.all)
    }

    var isAllSelected: Bool { !all.isEmpty && selected == all }

    mutating func toggle(_ id: ID) {
        guard all.contains(id) else { return }
        if selected.contains(id) { selected.remove(id) }
        else { selected.insert(id) }
    }

    mutating func toggleAll() {
        selected = isAllSelected ? [] : all
    }
}

struct MRLTaggedDocument: Codable, Identifiable, Equatable {
    let id: UUID
    let name: String
    var bookmark: Data
    var tags: Set<String>
    var sourceRecord: String? = nil
}

struct MRLTagArchive: Codable, Equatable {
    var version = 1
    var originSignature = "MrLiouWord"
    var catalog: [String] = []
    var documents: [MRLTaggedDocument] = []

    @discardableResult
    mutating func addTag(_ name: String) -> Bool {
        let value = name.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !value.isEmpty, value.utf8.count <= 1024 else { return false }
        guard !catalog.contains(value) else { return true }
        catalog.append(value)
        return true
    }

    // 加入標籤不移除原有標籤；沒有選取標籤時不做變更。
    @discardableResult
    mutating func apply(tags: Set<String>, to ids: Set<UUID>) -> Bool {
        let valid = tags.intersection(Set(catalog))
        guard documents.filter({ ids.contains($0.id) }).allSatisfy({
            $0.tags.union(valid).count <= 1000
        }) else { return false }
        for i in documents.indices where ids.contains(documents[i].id) {
            documents[i].tags.formUnion(valid)
        }
        return true
    }
}
