import XCTest
@testable import MRLTagCore

final class MRLTagTransferTests: XCTestCase {
    let digest = String(repeating: "a", count: 64)

    func testPortableRoundTripMergesOnlySameNameAndContent() throws {
        let first = UUID(), second = UUID(), third = UUID()
        var archive = MRLTagArchive()
        archive.documents = [
            .init(id: first, name: "原名.txt", bookmark: Data([1]), tags: ["舊"]),
            .init(id: second, name: "原名.txt", bookmark: Data([2]), tags: ["不變"]),
            .init(id: third, name: "別名.txt", bookmark: Data([3]), tags: [])
        ]
        let transfer = MRLTagTransfer(documents: [.init(name: "原名.txt", sha256: digest, tags: ["新"] )])
        let data = try JSONEncoder().encode(transfer)
        XCTAssertFalse(String(decoding: data, as: UTF8.self).contains("bookmark"))
        let decoded = try JSONDecoder().decode(MRLTagTransfer.self, from: data)
        let merged = try decoded.merging(into: archive,
            fingerprints: [first: digest, second: String(repeating: "b", count: 64), third: digest])
        XCTAssertEqual(merged.documents[0].tags, ["舊", "新"])
        XCTAssertEqual(merged.documents[1], archive.documents[1])
        XCTAssertEqual(merged.documents[2], archive.documents[2])
        XCTAssertEqual(try decoded.merging(into: merged, fingerprints: [first: digest]), merged)
        XCTAssertEqual(merged.originSignature, "MrLiouWord")
    }

    func testRejectsInvalidPacketBeforeMutation() throws {
        let valid = MRLTagTransfer.Entry(name: "原名.txt", sha256: digest, tags: ["新"])
        var unknown = MRLTagTransfer(documents: [valid])
        unknown.version = 2
        XCTAssertThrowsError(try unknown.validate())
        unknown.version = 1
        unknown.originSignature = "其他"
        XCTAssertThrowsError(try unknown.validate())
        for entry in [
            MRLTagTransfer.Entry(name: "../原名", sha256: digest, tags: []),
            .init(name: "原名", sha256: "broken", tags: []),
            .init(name: "原名", sha256: digest, tags: ["  "]),
            .init(name: "原名", sha256: digest, tags: [" 未正規化 "])
        ] {
            XCTAssertThrowsError(try MRLTagTransfer(documents: [valid, entry])
                .merging(into: MRLTagArchive(), fingerprints: [:]))
        }
    }

    func testNoFingerprintCannotApplyAndOriginalV1StillDecodes() throws {
        let archive = try JSONDecoder().decode(MRLTagArchive.self,
            from: Data(#"{"version":1,"originSignature":"MrLiouWord","catalog":[],"documents":[]}"#.utf8))
        let transfer = MRLTagTransfer(documents: [.init(name: "原名", sha256: digest, tags: ["新"])])
        XCTAssertEqual(try transfer.merging(into: archive, fingerprints: [:]), archive)
    }
}
