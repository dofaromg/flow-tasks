import UIKit
import UniformTypeIdentifiers

// origin_signature: MrLiouWord
final class MRLShareViewController: UIViewController {
    private let status = UILabel()
    private var started = false

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .systemBackground
        status.text = "將選取文件副本加入 MRL；不修改來源。"
        status.numberOfLines = 0
        let save = UIButton(type: .system)
        save.setTitle("加入 MRL", for: .normal)
        save.addTarget(self, action: #selector(saveFiles), for: .touchUpInside)
        let close = UIButton(type: .system)
        close.setTitle("關閉", for: .normal)
        close.addTarget(self, action: #selector(closeRequest), for: .touchUpInside)
        let stack = UIStackView(arrangedSubviews: [status, save, close])
        stack.axis = .vertical
        stack.spacing = 20
        stack.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(stack)
        NSLayoutConstraint.activate([
            stack.leadingAnchor.constraint(equalTo: view.safeAreaLayoutGuide.leadingAnchor, constant: 24),
            stack.trailingAnchor.constraint(equalTo: view.safeAreaLayoutGuide.trailingAnchor, constant: -24),
            stack.centerYAnchor.constraint(equalTo: view.centerYAnchor)
        ])
    }

    @objc private func closeRequest() {
        guard !started else { return }
        extensionContext?.completeRequest(returningItems: nil)
    }

    /// 一次一個 provider，避免大型多檔同時載入；每份成功副本獨立落盤。
    @objc private func saveFiles() {
        guard !started else { return }
        started = true
        let providers = (extensionContext?.inputItems as? [NSExtensionItem] ?? [])
            .flatMap { $0.attachments ?? [] }
        guard !providers.isEmpty, providers.count <= 1000 else {
            status.text = "沒有可匯入的文件，或超過 1000 份上限。"
            started = false
            return
        }
        receive(providers, index: 0, failures: 0)
    }

    private func receive(_ providers: [NSItemProvider], index: Int, failures: Int) {
        guard index < providers.count else {
            started = false
            status.text = "已加入 \(providers.count - failures)／\(providers.count) 份文件副本。\(failures > 0 ? "部分失敗，請從 Files 重選失敗文件。" : "")請關閉後開啟 MRL 的檔案與標籤。"
            return
        }
        let provider = providers[index]
        if provider.hasItemConformingToTypeIdentifier(UTType.fileURL.identifier) {
            provider.loadItem(forTypeIdentifier: UTType.fileURL.identifier, options: nil) { item, error in
                var failed = error != nil
                if let url = item as? URL, !failed {
                    do { try MRLShareInbox.receive(url) } catch { failed = true }
                } else { failed = true }
                let nextFailures = failures + (failed ? 1 : 0)
                DispatchQueue.main.async {
                    self.receive(providers, index: index + 1, failures: nextFailures)
                }
            }
            return
        }
        // 要求內容 representation，避免把 public.file-url 的文字表示當成文件內容。
        let type = provider.registeredTypeIdentifiers.first {
            $0 != UTType.fileURL.identifier && UTType($0)?.conforms(to: .data) == true
        }
        guard let type else {
            receive(providers, index: index + 1, failures: failures + 1)
            return
        }
        let suggestedName = provider.suggestedName
        provider.loadFileRepresentation(forTypeIdentifier: type) { url, error in
            var failed = error != nil
            if let url, !failed {
                do { try MRLShareInbox.receive(url, suggestedName: suggestedName) } catch { failed = true }
            } else { failed = true }
            let nextFailures = failures + (failed ? 1 : 0)
            DispatchQueue.main.async {
                self.receive(providers, index: index + 1, failures: nextFailures)
            }
        }
    }
}
