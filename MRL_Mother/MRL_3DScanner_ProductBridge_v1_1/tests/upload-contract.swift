import Foundation

// Compile with the actual production model; this is Codable validation, not iOS device acceptance.
@main
struct MRLUploadContractTest {
    static func main() throws {
        let bytes = try Data(contentsOf: URL(fileURLWithPath: CommandLine.arguments[1]))
        let response = try JSONDecoder().decode(MRLUploadResponse.self, from: bytes)
        precondition(response.ok && response.scanId == "unique" && response.uploaded == 1)
        let encoded = try JSONEncoder().encode(response)
        let object = try JSONSerialization.jsonObject(with: encoded) as! [String: Any]
        precondition(Set(object.keys) == Set(["ok", "scanId", "uploaded"]))
        print("PASS: actual MRLUploadResponse decodes and encodes the shared path-free API fixture")
    }
}
