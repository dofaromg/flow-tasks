import SwiftUI

struct ReconstructionBridgeView: View {
    let scan: Scan
    @StateObject private var client = MRLReconstructionClient()
    @State private var serverURL = ""
    @State private var status = "idle"
    @State private var jobId: String?
    @State private var errorText: String?

    var body: some View {
        Form {
            Section("DL580 Server") {
                TextField("http://DL580-IP:3050", text: $serverURL)
                    .textInputAutocapitalization(.never)
                    .autocorrectionDisabled()
                Button("Save Server URL") {
                    client.saveServerURL(serverURL)
                }
            }

            Section("Reconstruction") {
                Text("Status: \(status)")
                if let jobId { Text("Job: \(jobId)").font(.footnote) }
                if let errorText { Text(errorText).foregroundColor(.red) }

                Button("Upload Scan") {
                    Task { await uploadOnly() }
                }

                Button("Upload + Create Job") {
                    Task { await uploadAndRun() }
                }

                if let jobId {
                    Button("Refresh Job") {
                        Task { await refresh(jobId: jobId) }
                    }
                }
            }
        }
        .navigationTitle("MRL DL580 Bridge")
        .onAppear { serverURL = client.serverBaseURL }
    }

    private func uploadOnly() async {
        do {
            status = "uploading"
            _ = try await client.upload(scan: scan)
            status = "uploaded"
        } catch {
            status = "failed"
            errorText = error.localizedDescription
        }
    }

    private func uploadAndRun() async {
        do {
            status = "uploading"
            _ = try await client.upload(scan: scan)
            status = "creating job"
            let job = try await client.createJob(scanId: scan.id)
            jobId = job.jobId
            status = job.status
        } catch {
            status = "failed"
            errorText = error.localizedDescription
        }
    }

    private func refresh(jobId: String) async {
        do {
            let job = try await client.getJob(jobId: jobId)
            status = job.status
            errorText = job.message
        } catch {
            status = "failed"
            errorText = error.localizedDescription
        }
    }
}
