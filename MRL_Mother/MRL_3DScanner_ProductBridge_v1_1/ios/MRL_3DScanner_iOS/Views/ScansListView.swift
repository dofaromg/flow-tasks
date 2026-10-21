import SwiftUI

struct ScansListView: View {
    @EnvironmentObject private var store: ScanStore
    @State private var newScanName = ""
    @State private var errorText: String?

    var body: some View {
        NavigationView {
            List {
                Section("Create Scan Folder") {
                    TextField("scan name", text: $newScanName)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                    Button("Create") { createScan() }
                    if let errorText { Text(errorText).foregroundColor(.red) }
                }

                Section("Scans") {
                    if store.scans.isEmpty {
                        Text("No scans yet")
                            .foregroundColor(.secondary)
                    } else {
                        ForEach(store.scans) { scan in
                            NavigationLink(destination: ScanDetailView(scan: scan)) {
                                VStack(alignment: .leading, spacing: 4) {
                                    Text(scan.name).font(.headline)
                                    Text("images: \(scan.imageCount) · \(scan.sizeMB, specifier: "%.2f") MB")
                                        .font(.caption)
                                        .foregroundColor(.secondary)
                                }
                            }
                        }
                    }
                }
            }
            .navigationTitle("MRL 3D Scanner")
            .toolbar { Button("Reload") { store.load() } }
        }
    }

    private func createScan() {
        do {
            let name = newScanName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? defaultScanName() : newScanName
            let scan = try Scan.makeNew(base: store.base, name: name)
            store.save(scan)
            newScanName = ""
            errorText = nil
        } catch {
            errorText = error.localizedDescription
        }
    }

    private func defaultScanName() -> String {
        let f = DateFormatter()
        f.dateFormat = "yyyyMMdd_HHmmss"
        return "scan_\(f.string(from: Date()))"
    }
}

struct ScanDetailView: View {
    let scan: Scan

    var body: some View {
        Form {
            Section("Scan") {
                Text(scan.name)
                Text(scan.id.uuidString).font(.footnote)
                Text(scan.folder.path).font(.footnote)
                Text("raw: \(scan.rawFolder.path)").font(.footnote)
            }

            Section("DL580") {
                NavigationLink("Reconstruction Bridge") {
                    ReconstructionBridgeView(scan: scan)
                }
            }
        }
        .navigationTitle(scan.name)
    }
}
