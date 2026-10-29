import SwiftUI
import UniformTypeIdentifiers

@MainActor
struct MRLTagManagerView: View {
    @Environment(\.dismiss) private var dismiss
    @StateObject private var store = MRLTagStore()
    @State private var importing = false
    @State private var selectedDocuments = Set<UUID>()
    @State private var addingTags = false
    @State private var newTag = ""
    @State private var notice: String?

    private var documentSelection: MRLTagSelection<UUID> {
        MRLTagSelection(all: store.archive.documents.map(\.id), selected: selectedDocuments)
    }

    var body: some View {
        NavigationStack {
            List {
                Section {
                    Button("從「檔案」加入") { importing = true }
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
                if let notice { Text(notice).foregroundStyle(.secondary) }
            }
            .navigationTitle("檔案與標籤")
            .toolbar { Button("關閉") { dismiss() } }
            .fileImporter(isPresented: $importing, allowedContentTypes: [.item],
                allowsMultipleSelection: true) { result in
                switch result {
                case .success(let urls): store.register(urls)
                case .failure(let error): store.errorMessage = error.localizedDescription
                }
            }
            .sheet(isPresented: $addingTags) {
                MRLTagPickerView(tags: store.archive.catalog) { tags in
                    if store.apply(tags: tags, to: documentSelection.selected) {
                        notice = "已儲存 \(documentSelection.selected.count) 個檔案的 MRL 標籤。"
                        return true
                    }
                    return false
                }
            }
            .alert("儲存狀態", isPresented: Binding(
                get: { store.errorMessage != nil },
                set: { if !$0 { store.errorMessage = nil } }
            )) { Button("確定") { store.errorMessage = nil } }
            message: { Text(store.errorMessage ?? "") }
        }
    }
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
