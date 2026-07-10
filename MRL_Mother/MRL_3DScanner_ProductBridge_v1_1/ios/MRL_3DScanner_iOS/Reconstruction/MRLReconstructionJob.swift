import Foundation

struct MRLReconstructionJob: Identifiable, Codable, Equatable {
    var id: String { jobId }
    let jobId: String
    let scanId: UUID
    let status: String
    let mode: String
    let createdAt: String
    let updatedAt: String?
    let message: String?
    let outputFiles: [String]?
}

struct MRLUploadResponse: Codable {
    let ok: Bool
    let scanId: String
    let uploaded: Int
    let manifestPath: String
}

struct MRLJobCreateResponse: Codable {
    let ok: Bool
    let jobId: String
    let status: String
}
