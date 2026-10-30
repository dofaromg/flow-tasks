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
            let before = invalid.archive
            precondition(!invalid.apply(tags: ["不得覆寫"], to: [UUID()]))
            invalid.addTag("不得覆寫")
            precondition(invalid.archive == before)
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
        // 真實失敗寫入之後恢復：原 archive、記憶體及 blocker 均須保留。
        let recoverDirectory = root.appendingPathComponent("recover")
        try manager.createDirectory(at: recoverDirectory, withIntermediateDirectories: false)
        let recoverLocation = recoverDirectory.appendingPathComponent("archive.json")
        let recover = MRLTagStore(location: recoverLocation)
        let file = root.appendingPathComponent("登錄.txt")
        try bytes.write(to: file)
        precondition(recover.register([file, file]))
        precondition(recover.archive.documents.count == 1)
        let recovered = MRLTagStore(location: recoverLocation)
        precondition(recovered.register([file]))
        precondition(recovered.archive.documents.count == 1)
        recover.addTag("新")
        let id = recover.archive.documents[0].id
        let beforeWrite = recover.archive
        let beforeBytes = try Data(contentsOf: recoverLocation)
        let backup = root.appendingPathComponent("backup")
        try manager.moveItem(at: recoverDirectory, to: backup)
        let blockerBytes = Data("保留 blocker".utf8)
        try blockerBytes.write(to: recoverDirectory)
        precondition(!recover.apply(tags: ["新"], to: [id]))
        precondition(recover.archive == beforeWrite && recover.errorMessage != nil)
        let preservedArchive = try Data(contentsOf: backup.appendingPathComponent("archive.json"))
        let preservedBlocker = try Data(contentsOf: recoverDirectory)
        precondition(preservedArchive == beforeBytes && preservedBlocker == blockerBytes)
        try manager.removeItem(at: recoverDirectory)
        try manager.moveItem(at: backup, to: recoverDirectory)
        precondition(recover.apply(tags: ["新"], to: [id]))
        precondition(recover.errorMessage == nil)
        precondition(MRLTagStore(location: recoverLocation).archive == recover.archive)

        // 重複 UUID 的資料不能成為可覆寫的主檔。
        var duplicate = recover.archive
        duplicate.documents.append(duplicate.documents[0])
        let duplicateBytes = try JSONEncoder().encode(duplicate)
        try duplicateBytes.write(to: recoverLocation)
        let invalidIDs = MRLTagStore(location: recoverLocation)
        invalidIDs.addTag("不得覆寫")
        let afterDuplicate = try Data(contentsOf: recoverLocation)
        precondition(invalidIDs.errorMessage != nil && afterDuplicate == duplicateBytes)

        // 同名 provenance 來源仍須原名原內容保存，不能與 metadata 互相覆蓋。
        let reservedName = root.appendingPathComponent(".MRL_source.json")
        try bytes.write(to: reservedName)
        try MRLShareInbox.receive(reservedName, inboxRoot: inbox)
        let envelopes = try manager.contentsOfDirectory(at: inbox, includingPropertiesForKeys: nil)
        let reservedCopy = try envelopes.first { $0 != received[0] }.map {
            try Data(contentsOf: $0.appendingPathComponent("MRL_Payload/.MRL_source.json"))
        }
        precondition(reservedCopy == bytes)
        print("MRL store: restart/corrupt/version/origin/write recovery/dedup/provenance collision PASS")
    }
}

