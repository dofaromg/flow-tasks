import Foundation

// origin_signature: MrLiouWord
@main
struct MRLTagStoreRegression {
    @MainActor static func main() throws {
        let manager = FileManager.default
        let root = manager.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try manager.createDirectory(at: root, withIntermediateDirectories: false)
        defer { try? manager.removeItem(at: root) }
        let location = root.appendingPathComponent("MRL_TagArchive.json")
        let store = MRLTagStore(location: location)
        store.addTag("既有")
        precondition(MRLTagStore(location: location).archive.catalog == ["既有"])
        for bytes in [Data("broken".utf8),
            Data(#"{"version":2,"originSignature":"MrLiouWord","catalog":[],"documents":[]}"#.utf8),
            Data(#"{"version":1,"originSignature":"其他","catalog":[],"documents":[]}"#.utf8)] {
            try bytes.write(to: location)
            let invalid = MRLTagStore(location: location)
            invalid.addTag("不得覆寫")
            precondition(invalid.errorMessage != nil)
            let preserved = try Data(contentsOf: location)
            precondition(preserved == bytes)
        }
        let blocked = MRLTagStore(location: root.appendingPathComponent("missing/archive.json"))
        try Data([1]).write(to: root.appendingPathComponent("missing"))
        blocked.addTag("不能儲存")
        precondition(blocked.archive.catalog.isEmpty && blocked.errorMessage != nil)
        let inbox = root.appendingPathComponent("inbox")
        try manager.createDirectory(at: inbox, withIntermediateDirectories: false)
        let original = root.appendingPathComponent("原名.txt")
        let bytes = Data("MRL 原件".utf8)
        try bytes.write(to: original)
        try MRLShareInbox.receive(original, inboxRoot: inbox)
        let received = try manager.contentsOfDirectory(at: inbox, includingPropertiesForKeys: nil)
        precondition(received.count == 1 && UUID(uuidString: received[0].lastPathComponent) != nil)
        try manager.removeItem(at: original)
        let copy = try Data(contentsOf: received[0].appendingPathComponent("MRL_Payload/原名.txt"))
        precondition(copy == bytes)
        let provenance = try Data(contentsOf: received[0].appendingPathComponent(".MRL_source.json"))
        precondition(String(decoding: provenance, as: UTF8.self).contains("MrLiouWord"))
        do { try MRLShareInbox.receive(root, inboxRoot: inbox); preconditionFailure("directory must fail") }
        catch { /* 不支持的來源沒有 ready 目錄 */ }
        let remaining = try manager.contentsOfDirectory(atPath: inbox.path)
        precondition(remaining.count == 1)
        let reservedName = root.appendingPathComponent(".MRL_source.json")
        try bytes.write(to: reservedName)
        try MRLShareInbox.receive(reservedName, inboxRoot: inbox)
        let envelopes = try manager.contentsOfDirectory(at: inbox, includingPropertiesForKeys: nil)
        let reservedCopy = try envelopes.first { $0 != received[0] }.map {
            try Data(contentsOf: $0.appendingPathComponent("MRL_Payload/.MRL_source.json"))
        }
        precondition(reservedCopy == bytes)
        print("MRL store: restart/corrupt/version/origin/write failure PASS")
    }
}
