import Foundation
import Combine

enum MRLReconstructionClientError: LocalizedError {
    case badServerURL(String)
    case noCaptureFiles(String)

    var errorDescription: String? {
        switch self {
        case .badServerURL(let value): return "Invalid DL580 server URL: \(value)"
        case .noCaptureFiles(let path): return "No supported image files found in raw folder: \(path)"
        }
    }
}

final class MRLReconstructionClient: ObservableObject {
    @Published var serverBaseURL: String = UserDefaults.standard.string(forKey: "MRL_DL580_ServerURL") ?? "http://127.0.0.1:3050"

    func saveServerURL(_ url: String) {
        serverBaseURL = normalized(url)
        UserDefaults.standard.set(serverBaseURL, forKey: "MRL_DL580_ServerURL")
    }

    func upload(scan: Scan) async throws -> MRLUploadResponse {
        let boundary = "MRLBOUNDARY-\(UUID().uuidString)"
        var request = URLRequest(url: try endpoint("/api/scans/upload"))
        request.httpMethod = "POST"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        request.setValue(scan.id.uuidString, forHTTPHeaderField: "X-MRL-Scan-ID")
        request.setValue(scan.name, forHTTPHeaderField: "X-MRL-Scan-Name")

        let files = (try? FileManager.default.imageFileURLs(in: scan.rawFolder)) ?? []
        guard !files.isEmpty else { throw MRLReconstructionClientError.noCaptureFiles(scan.rawFolder.path) }

        var body = Data()
        for file in files {
            let data = try Data(contentsOf: file)
            body.appendString("--\(boundary)\r\n")
            body.appendString("Content-Disposition: form-data; name=\"files\"; filename=\"\(file.lastPathComponent)\"\r\n")
            body.appendString("Content-Type: \(mimeType(for: file))\r\n\r\n")
            body.append(data)
            body.appendString("\r\n")
        }
        body.appendString("--\(boundary)--\r\n")
        request.httpBody = body

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode) else {
            throw URLError(.badServerResponse)
        }
        return try JSONDecoder().decode(MRLUploadResponse.self, from: data)
    }

    func createJob(scanId: UUID, mode: String = "auto") async throws -> MRLJobCreateResponse {
        var request = URLRequest(url: try endpoint("/api/reconstruction/jobs"))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONSerialization.data(withJSONObject: ["scanId": scanId.uuidString, "mode": mode])
        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode) else { throw URLError(.badServerResponse) }
        return try JSONDecoder().decode(MRLJobCreateResponse.self, from: data)
    }

    func getJob(jobId: String) async throws -> MRLReconstructionJob {
        let (data, response) = try await URLSession.shared.data(from: try endpoint("/api/reconstruction/jobs/\(jobId)"))
        guard let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode) else { throw URLError(.badServerResponse) }
        return try JSONDecoder().decode(MRLReconstructionJob.self, from: data)
    }

    private func endpoint(_ path: String) throws -> URL {
        let base = normalized(serverBaseURL)
        guard let url = URL(string: "\(base)\(path)") else { throw MRLReconstructionClientError.badServerURL(serverBaseURL) }
        return url
    }

    private func normalized(_ value: String) -> String {
        var v = value.trimmingCharacters(in: .whitespacesAndNewlines)
        while v.hasSuffix("/") { v.removeLast() }
        return v
    }

    private func mimeType(for file: URL) -> String {
        switch file.pathExtension.lowercased() {
        case "png": return "image/png"
        case "heic": return "image/heic"
        case "jpg", "jpeg": return "image/jpeg"
        default: return "application/octet-stream"
        }
    }
}

private extension Data {
    mutating func appendString(_ string: String) {
        append(string.data(using: .utf8)!)
    }
}
