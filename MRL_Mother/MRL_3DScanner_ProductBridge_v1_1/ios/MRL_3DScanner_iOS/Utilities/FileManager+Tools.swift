import Foundation

extension FileManager {
    func allocatedSizeOfDirectory(at url: URL) throws -> Int64 {
        var total: Int64 = 0
        guard let enumerator = self.enumerator(at: url, includingPropertiesForKeys: [.isRegularFileKey, .totalFileAllocatedSizeKey, .fileAllocatedSizeKey]) else { return 0 }
        for case let fileURL as URL in enumerator {
            let values = try fileURL.resourceValues(forKeys: [.isRegularFileKey, .totalFileAllocatedSizeKey, .fileAllocatedSizeKey])
            if values.isRegularFile ?? false { total += Int64(values.totalFileAllocatedSize ?? values.fileAllocatedSize ?? 0) }
        }
        return total
    }
    func imageFileURLs(in folder: URL) throws -> [URL] {
        guard fileExists(atPath: folder.path) else { return [] }
        let allowed = ["jpg", "jpeg", "png", "heic"]
        return try contentsOfDirectory(at: folder, includingPropertiesForKeys: nil).filter { allowed.contains($0.pathExtension.lowercased()) }.sorted { $0.lastPathComponent < $1.lastPathComponent }
    }
}
