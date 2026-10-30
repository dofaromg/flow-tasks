import SwiftUI
import UniformTypeIdentifiers
import UIKit

@MainActor
struct MRLTagManagerView: View {
    @Environment(\.dismiss) private var dismiss
    @StateObject private var store = MRLTagStore()
    @State private var importing = false
    @State private var selectedDocuments = Set<UUID>()
    @State private var addingTags = false
    @State private var newTag = ""
    @State private var notice: String?
    @Environment(\.scenePhase) private var scenePhase
    @State private var importingTags = false
    @State private var shareDirectory: URL?
    @State private var share: MRLSharePayload?

    private var documentSelection: MRLTagSelection<UUID> {
        MRLTagSelection(all: store.archive.documents.map(\.id), selected: selectedDocuments)
    }

    var body: some View {
        NavigationStack {
            List {
                Section {
                    Button("從「檔案」加入") { importingTags = false; importing = true }
                    Button("讀取分享收件匣") { notice = nil; store.receiveSharedFiles() }
                    Text("標籤儲存在 MRL App 內；不修改原始檔案或 iPhone 系統標籤。")
                        .font(.footnote).foregroundStyle(.secondary)
                }
                Section {
                    HStack {
                        Button(documentSelection.isAllSelected ? "取消全選" : "全選檔案") {
                            var selection = documentSelection
                            selection.toggleAll()
                            selectedDocuments = selection.selected
                        }.disabled(store.archive.documents.isEmpty)
                        Spacer()
                        Text("已選 \(documentSelection.selected.count)／\(store.archive.documents.count)")
                            .font(.footnote)
                    }
                    ForEach(store.archive.documents) { document in
                        Button {
                            var selection = documentSelection
                            selection.toggle(document.id)
                            selectedDocuments = selection.selected
                        } label: {
                            HStack {
                                Image(systemName: selectedDocuments.contains(document.id)
                                    ? "checkmark.circle.fill" : "circle")
                                VStack(alignment: .leading) {
                                    Text(document.name).foregroundStyle(.primary)
                                    Text(document.tags.sorted().joined(separator: "、"))
                                        .font(.caption).foregroundStyle(.secondary)
                                }
                            }.frame(minHeight: 44)
                        }
                        .accessibilityValue(selectedDocuments.contains(document.id) ? "已選取" : "未選取")
                    }
                } header: { Text("MRL 檔案清單") }
                Section("標籤目錄") {
                    HStack {
                        TextField("新增標籤", text: $newTag)
                        Button("新增") {
                            store.addTag(newTag)
                            if store.errorMessage == nil { newTag = "" }
                        }.disabled(newTag.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                    }
                    ForEach(store.archive.catalog, id: \.self) { Text($0) }
                }
                Button("加入標籤") { addingTags = true }
                    .disabled(selectedDocuments.isEmpty || store.archive.catalog.isEmpty)
                Button("分享所選文件與 MRL 標籤") {
                    notice = nil
                    do {
                        let exported = try store.exportFiles(documentSelection.selected)
                        shareDirectory = exported.directory
                        share = MRLSharePayload(directory: exported.directory, files: exported.files)
                    } catch { store.errorMessage = "無法分享，請重新選取失效文件：\(error.localizedDescription)" }
                }.disabled(selectedDocuments.isEmpty)
                Button("匯入 MRL 標籤到所選文件") { notice = nil; importingTags = true; importing = true }
                    .disabled(selectedDocuments.isEmpty)
                if let notice { Text(notice).foregroundStyle(.secondary) }
            }
            .navigationTitle("檔案與標籤")
            .onAppear { store.receiveSharedFiles() }
            .onChange(of: scenePhase) { phase in
                if phase == .active { store.receiveSharedFiles() }
            }
            .toolbar { Button("關閉") { dismiss() } }
            .fileImporter(isPresented: $importing, allowedContentTypes: importingTags ? [.json] : [.item],
                allowsMultipleSelection: !importingTags) { result in
                switch result {
                case .success(let urls):
                    notice = nil
                    if importingTags, let url = urls.first {
                        if let count = store.importTransfer(url, to: documentSelection.selected) {
                            notice = "已配對 \(count) 份文件並保留既有標籤；未修改系統標籤。"
                        }
                    } else { store.register(urls) }
                case .failure(let error): store.errorMessage = error.localizedDescription
                }
            }
            .sheet(isPresented: $addingTags) {
                MRLTagPickerView(tags: store.archive.catalog) { tags in
                    notice = nil
                    if store.apply(tags: tags, to: documentSelection.selected) {
                        notice = "已儲存 \(documentSelection.selected.count) 個檔案的 MRL 標籤。"
                        return true
                    }
                    return false
                }
            }
            .sheet(item: $share, onDismiss: {
                if let shareDirectory { try? FileManager.default.removeItem(at: shareDirectory) }
                shareDirectory = nil
            }) { payload in
                MRLActivityView(payload: payload)
            }
            .alert("儲存狀態", isPresented: Binding(
                get: { store.errorMessage != nil },
                set: { if !$0 { store.errorMessage = nil } }
            )) { Button("確定") { store.errorMessage = nil } }
            message: { Text(store.errorMessage ?? "") }
        }
    }
}

private struct MRLSharePayload: Identifiable {
    let id = UUID()
    let directory: URL
    let files: [URL]
}

private struct MRLActivityView: UIViewControllerRepresentable {
    let payload: MRLSharePayload
    func makeUIViewController(context: Context) -> UIActivityViewController {
        let controller = UIActivityViewController(activityItems: payload.files, applicationActivities: nil)
        controller.completionWithItemsHandler = { _, _, _, _ in
            try? FileManager.default.removeItem(at: payload.directory)
        }
        return controller
    }
    func updateUIViewController(_ controller: UIActivityViewController, context: Context) {}
}

private struct MRLTagPickerView: View {
    @Environment(\.dismiss) private var dismiss
    let tags: [String]
    let onApply: (Set<String>) -> Bool
    @State private var selected = Set<String>()
    @State private var failed = false

    private var selection: MRLTagSelection<String> {
        MRLTagSelection(all: tags, selected: selected)
    }

    var body: some View {
        NavigationStack {
            List {
                HStack {
                    Button(selection.isAllSelected ? "取消全選" : "全選") {
                        var updated = selection
                        updated.toggleAll()
                        selected = updated.selected
                    }.disabled(tags.isEmpty)
                    Spacer()
                    Text("已選 \(selection.selected.count)／\(tags.count)").font(.footnote)
                }
                ForEach(tags, id: \.self) { tag in
                    Button {
                        var updated = selection
                        updated.toggle(tag)
                        selected = updated.selected
                    } label: {
                        Label(tag, systemImage: selected.contains(tag)
                            ? "checkmark.circle.fill" : "circle")
                            .frame(minHeight: 44)
                    }
                    .accessibilityValue(selected.contains(tag) ? "已選取" : "未選取")
                }
                if failed { Text("尚未儲存，請取消後檢查錯誤訊息再重試。") }
            }
            .navigationTitle("加入標籤")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("取消") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("套用") {
                        if onApply(selection.selected) { dismiss() }
                        else { failed = true }
                    }.disabled(selection.selected.isEmpty)
                }
            }
        }
    }
}

