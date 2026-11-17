import XCTest
@testable import MRLTagCore

final class MRLTagCoreTests: XCTestCase {
    func testAllIncludesOffscreenItemsAndIndividualToggle() {
        var selection = MRLTagSelection(all: Array(0..<1000), selected: [7, 2001])
        XCTAssertEqual(selection.selected, [7])
        selection.toggleAll()
        XCTAssertEqual(selection.selected.count, 1000)
        XCTAssertTrue(selection.isAllSelected)
        selection.toggle(999)
        XCTAssertFalse(selection.isAllSelected)
        selection.toggleAll()
        XCTAssertTrue(selection.isAllSelected)
        selection.toggleAll()
        XCTAssertTrue(selection.selected.isEmpty)
        selection.toggle(2001)
        XCTAssertTrue(selection.selected.isEmpty)
    }

    func testEmptyAndDuplicateItems() {
        var empty = MRLTagSelection<String>(all: [])
        empty.toggleAll()
        XCTAssertFalse(empty.isAllSelected)
        var duplicates = MRLTagSelection(all: ["世界模型核心", "世界模型核心"])
        duplicates.toggleAll()
        XCTAssertEqual(duplicates.selected.count, 1)
    }

    func testBatchPreservesExistingAndUnselectedDocumentsAfterRoundTrip() throws {
        let first = UUID(), second = UUID()
        var archive = MRLTagArchive()
        archive.addTag(" 新標籤 ")
        archive.addTag("新標籤")
        archive.addTag("  ")
        archive.documents = [
            MRLTaggedDocument(id: first, name: "原名.zip", bookmark: Data([1]), tags: ["既有"]),
            MRLTaggedDocument(id: second, name: "不修改.txt", bookmark: Data([2]), tags: ["保留"])
        ]
        archive.apply(tags: ["新標籤", "不存在"], to: [first])
        XCTAssertEqual(archive.documents[0].tags, ["既有", "新標籤"])
        XCTAssertEqual(archive.documents[1].tags, ["保留"])
        XCTAssertEqual(archive.catalog, ["新標籤"])
        let restored = try JSONDecoder().decode(MRLTagArchive.self,
            from: JSONEncoder().encode(archive))
        XCTAssertEqual(restored, archive)
        let before = archive
        archive.apply(tags: [], to: [first, second])
        XCTAssertEqual(before, archive)
    }
}
