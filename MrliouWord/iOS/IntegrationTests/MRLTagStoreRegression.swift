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
        let inboxStore = MRLTagStore(location: root.appendingPathComponent("inbox-archive.json"))
        let imports = root.appendingPathComponent("imports")
        try manager.createDirectory(at: imports, withIntermediateDirectories: false)
        let destination = imports.appendingPathComponent(received[0].lastPathComponent)
        try manager.copyItem(at: received[0], to: destination)
        let target = destination.appendingPathComponent("MRL_Payload/原名.txt")
        let conflict = Data("保留不同內容".utf8)
        try conflict.write(to: target)
        inboxStore.receiveSharedFiles(inboxRoot: inbox, importsRoot: imports)
        precondition(inboxStore.errorMessage != nil)
        precondition(manager.fileExists(atPath: received[0].path))
        let keptConflict = try Data(contentsOf: target)
        precondition(keptConflict == conflict)
        try manager.removeItem(at: target)
        inboxStore.receiveSharedFiles(inboxRoot: inbox, importsRoot: imports)
        precondition(inboxStore.archive.documents.map(\.name) == ["原名.txt"])
        precondition(!manager.fileExists(atPath: received[0].path))
        let repaired = try Data(contentsOf: target)
        precondition(repaired == bytes)
        // NSItemProvider 暫存 URL 與原名不同時仍保留來源名稱。
        try MRLShareInbox.receive(target, suggestedName: "分享原名.txt", inboxRoot: inbox)
        let named = try manager.contentsOfDirectory(at: inbox, includingPropertiesForKeys: nil)[0]
        precondition(manager.fileExists(atPath: named.appendingPathComponent("MRL_Payload/分享原名.txt").path))
        try manager.removeItem(at: named)
        try MRLShareInbox.receive(target, suggestedName: "../非法.txt", inboxRoot: inbox)
        do { try MRLShareInbox.receive(root, inboxRoot: inbox); preconditionFailure("directory must fail") }
        catch { /* 不支持的來源沒有 ready 目錄 */ }
        let remaining = try manager.contentsOfDirectory(atPath: inbox.path)
        precondition(remaining.count == 1)
        try manager.removeItem(at: inbox.appendingPathComponent(remaining[0]))
        // 超長 ASCII／多位元名稱由目的檔案系統拒絕後回退；原名不可截斷。
        for longName in [String(repeating: "a", count: 4096) + ".txt",
                         String(repeating: "原", count: 4096) + ".txt"] {
            try MRLShareInbox.receive(target, suggestedName: longName, inboxRoot: inbox)
            let envelope = try manager.contentsOfDirectory(at: inbox, includingPropertiesForKeys: nil)[0]
            let payload = envelope.appendingPathComponent("MRL_Payload")
            let files = try manager.contentsOfDirectory(at: payload, includingPropertiesForKeys: nil)
            precondition(files.count == 1 && files[0].lastPathComponent == target.lastPathComponent)
            let copiedBytes = try Data(contentsOf: files[0])
            precondition(copiedBytes == bytes)
            let record = try JSONSerialization.jsonObject(with: Data(contentsOf:
                envelope.appendingPathComponent(".MRL_source.json"))) as! [String: String]
            precondition(record["original_name"] == longName)
            precondition(record["stored_name"] == target.lastPathComponent)
            precondition(record["origin_signature"] == "MrLiouWord")
            try manager.removeItem(at: envelope)
        }
        let sourceAfterFallback = try Data(contentsOf: target)
        precondition(sourceAfterFallback == bytes)

        // 可重現 stale 更新失敗：保留舊 bookmark、標籤、來源並繼續直接／收件匣登錄。
        let staleLocation = root.appendingPathComponent("stale-archive.json")
        let staleSeed = MRLTagStore(location: staleLocation)
        precondition(staleSeed.register([target], sourceRecord: "既有來源"))
        let oldID = staleSeed.archive.documents[0].id
        precondition(staleSeed.apply(tags: ["既有"], to: [oldID]))
        let oldDocument = staleSeed.archive.documents[0]
        var refreshAttempts = 0
        let staleStore = MRLTagStore(location: staleLocation, resolveBookmark: { data in
            if data == oldDocument.bookmark { return (target, true) }
            var stale = false
            return (try URL(resolvingBookmarkData: data, options: [], relativeTo: nil,
                bookmarkDataIsStale: &stale), stale)
        }, makeBookmark: { url in
            if url == target {
                refreshAttempts += 1
                throw CocoaError(.fileReadNoPermission)
            }
            return try url.bookmarkData(options: .minimalBookmark,
                includingResourceValuesForKeys: nil, relativeTo: nil)
        })
        let newFile = root.appendingPathComponent("新文件.txt")
        try bytes.write(to: newFile)
        precondition(staleStore.register([target, newFile, newFile]))
        precondition(refreshAttempts == 1 && staleStore.archive.documents.count == 2)
        precondition(staleStore.archive.documents[0] == oldDocument)
        try MRLShareInbox.receive(newFile, inboxRoot: inbox)
        staleStore.receiveSharedFiles(inboxRoot: inbox, importsRoot: root.appendingPathComponent("stale-imports"))
        precondition(refreshAttempts == 2 && staleStore.archive.documents.count == 3)
        precondition(staleStore.archive.documents[0] == oldDocument)
        let drained = try manager.contentsOfDirectory(atPath: inbox.path)
        precondition(drained.isEmpty && staleStore.errorMessage == nil)
        precondition(MRLTagStore(location: staleLocation).archive == staleStore.archive)
        let renewed = Data("renewed bookmark".utf8)
        let refreshing = MRLTagStore(location: staleLocation,
            resolveBookmark: { _ in (target, true) }, makeBookmark: { _ in renewed })
        precondition(refreshing.register([]))
        precondition(refreshing.archive.documents.allSatisfy { $0.bookmark == renewed })
        precondition(MRLTagStore(location: staleLocation).archive == refreshing.archive)
        print("MRL store: stale refresh isolation/success and long-name fallback PASS")
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
        let reservedCopy = try envelopes.first.map {
            try Data(contentsOf: $0.appendingPathComponent("MRL_Payload/.MRL_source.json"))
        }
        precondition(reservedCopy == bytes)
        print("MRL store: restart/corrupt/version/origin/write recovery/dedup/provenance collision PASS")
    }
}
