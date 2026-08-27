// mrliouai_core/include/mrl/vault.hpp
// Vault — 沙箱檔案系統
// origin_signature: MrLiouWord
// 對應規格：MRL_Mother/04_runtime/flowcore_loop.py Vault 類別 (lines 304-391)
//   - root-restricted 路徑解析，防 traversal
//   - 原子寫入（.tmp → rename）
//   - SHA-256 checksum
//   - 大小上限與列表截斷
//
// 法則：不刪檔。本 Vault 不提供 delete/unlink 介面。
#pragma once

#include <sys/stat.h>
#include <unistd.h>

#include <cstdio>
#include <filesystem>
#include <fstream>
#include <string>
#include <vector>

#include "base64.hpp"
#include "json.hpp"
#include "merkle.hpp"
#include "sha256.hpp"

namespace mrl {

namespace fs = std::filesystem;

class Vault {
public:
    static constexpr size_t MAX_READ_BYTES = 8 * 1024 * 1024;
    static constexpr size_t MAX_LIST_ENTRIES = 2000;

    explicit Vault(std::string root, Tracer* tracer = nullptr)
        : tracer_(tracer) {
        std::error_code ec;
        fs::create_directories(root, ec);
        root_ = fs::canonical(root, ec);
        if (ec) root_ = fs::absolute(root);
    }

    const fs::path& root() const { return root_; }

    struct Resolved {
        bool ok = false;
        std::string error;
        fs::path path;
    };

    // 路徑解析 + 沙箱檢查。拒絕跳出 root 的任何路徑。
    // must_exist=true  → 目標必須已存在（讀取類操作）
    // must_exist=false → 目標可不存在，但解析後仍須落在 root 內（寫入類操作）
    Resolved resolve(const std::string& rel, bool must_exist) const {
        Resolved r;

        if (rel.find('\0') != std::string::npos) {
            r.error = "null_byte_in_path";
            return r;
        }

        fs::path p = rel.empty() || rel == "." ? root_ : (root_ / fs::path(rel).relative_path());

        std::error_code ec;
        if (must_exist) {
            fs::path canon = fs::canonical(p, ec);
            if (ec) {
                r.error = "not_found";
                return r;
            }
            if (!within(canon)) {
                r.error = "path_escapes_vault_root";
                return r;
            }
            r.ok = true;
            r.path = canon;
            return r;
        }

        // 目標不必存在：找出最近的既存祖先，canonical 它（解掉 symlink），
        // 再把剩餘尚未存在的路徑段逐一 lexical 附加。任一步跳出 root 即拒絕。
        // 這樣 mkdir("a/b/c") 在 a、b 都還不存在時也能通過。
        fs::path lexical = p.lexically_normal();

        fs::path existing = lexical;
        std::vector<fs::path> pending;
        while (!existing.empty() && !fs::exists(existing, ec)) {
            if (!existing.has_parent_path() || existing.parent_path() == existing) break;
            pending.push_back(existing.filename());
            existing = existing.parent_path();
        }

        fs::path base = fs::canonical(existing, ec);
        if (ec) {
            r.error = "no_existing_ancestor";
            return r;
        }
        if (!within(base)) {
            r.error = "path_escapes_vault_root";
            return r;
        }

        for (auto it = pending.rbegin(); it != pending.rend(); ++it) {
            const std::string seg = it->string();
            if (seg == "..") {
                r.error = "path_escapes_vault_root";
                return r;
            }
            if (seg == "." || seg.empty()) continue;
            base /= *it;
        }

        if (!within(base)) {
            r.error = "path_escapes_vault_root";
            return r;
        }
        r.ok = true;
        r.path = base;
        return r;
    }

    // ── list ──
    Json list(const std::string& rel) const {
        Json out = Json::object();
        auto rv = resolve(rel, true);
        if (!rv.ok) {
            out["ok"] = false;
            out["error"] = rv.error;
            return out;
        }
        std::error_code ec;
        if (!fs::is_directory(rv.path, ec)) {
            out["ok"] = false;
            out["error"] = "not_a_directory";
            return out;
        }

        Json entries = Json::array();
        size_t n = 0;
        bool truncated = false;
        for (fs::directory_iterator it(rv.path, ec), end; it != end; it.increment(ec)) {
            if (ec) break;
            if (n >= MAX_LIST_ENTRIES) { truncated = true; break; }
            Json e = Json::object();
            e["name"] = it->path().filename().string();
            std::error_code e2;
            bool is_dir = it->is_directory(e2);
            e["type"] = std::string(is_dir ? "dir" : "file");
            e["size"] = is_dir ? 0LL : static_cast<long long>(fs::file_size(it->path(), e2));
            e["rel"] = fs::relative(it->path(), root_, e2).string();
            entries.push(e);
            ++n;
        }

        out["ok"] = true;
        out["path"] = fs::relative(rv.path, root_, ec).string();
        out["count"] = static_cast<long long>(n);
        out["truncated"] = truncated;
        out["entries"] = entries;
        out["origin_signature"] = std::string("MrLiouWord");
        return out;
    }

    // ── read_text ──
    Json read_text(const std::string& rel) const {
        Json out = Json::object();
        auto rv = resolve(rel, true);
        if (!rv.ok) { out["ok"] = false; out["error"] = rv.error; return out; }

        std::error_code ec;
        if (!fs::is_regular_file(rv.path, ec)) {
            out["ok"] = false; out["error"] = "not_a_regular_file"; return out;
        }
        auto sz = fs::file_size(rv.path, ec);
        if (sz > MAX_READ_BYTES) {
            out["ok"] = false;
            out["error"] = "file_too_large";
            out["size"] = static_cast<long long>(sz);
            out["limit"] = static_cast<long long>(MAX_READ_BYTES);
            return out;
        }

        std::ifstream f(rv.path, std::ios::binary);
        std::string body((std::istreambuf_iterator<char>(f)), std::istreambuf_iterator<char>());

        out["ok"] = true;
        out["path"] = fs::relative(rv.path, root_, ec).string();
        out["size"] = static_cast<long long>(body.size());
        out["sha256"] = SHA256::hex(body);
        out["content"] = body;
        out["origin_signature"] = std::string("MrLiouWord");
        return out;
    }

    // ── read_bytes (base64) ──
    Json read_bytes_b64(const std::string& rel) const {
        Json out = Json::object();
        auto rv = resolve(rel, true);
        if (!rv.ok) { out["ok"] = false; out["error"] = rv.error; return out; }

        std::error_code ec;
        auto sz = fs::file_size(rv.path, ec);
        if (ec || sz > MAX_READ_BYTES) {
            out["ok"] = false; out["error"] = "file_too_large_or_unreadable"; return out;
        }

        std::ifstream f(rv.path, std::ios::binary);
        std::string body((std::istreambuf_iterator<char>(f)), std::istreambuf_iterator<char>());

        out["ok"] = true;
        out["path"] = fs::relative(rv.path, root_, ec).string();
        out["size"] = static_cast<long long>(body.size());
        out["sha256"] = SHA256::hex(body);
        out["base64"] = base64_encode(body);
        return out;
    }

    // ── write_text（原子寫入） ──
    Json write_text(const std::string& rel, const std::string& content) {
        Json out = Json::object();
        auto rv = resolve(rel, false);
        if (!rv.ok) { out["ok"] = false; out["error"] = rv.error; return out; }

        std::error_code ec;
        bool existed = fs::exists(rv.path, ec);

        std::string tmp = rv.path.string() + ".tmp";
        {
            std::ofstream f(tmp, std::ios::binary | std::ios::trunc);
            if (!f) { out["ok"] = false; out["error"] = "cannot_open_tmp"; return out; }
            f.write(content.data(), static_cast<std::streamsize>(content.size()));
            f.flush();
            if (!f) { out["ok"] = false; out["error"] = "write_failed"; return out; }
        }
        if (std::rename(tmp.c_str(), rv.path.string().c_str()) != 0) {
            out["ok"] = false; out["error"] = "atomic_rename_failed"; return out;
        }

        std::string sha = SHA256::hex(content);
        if (tracer_) {
            Json p = Json::object();
            p["path"] = fs::relative(rv.path, root_, ec).string();
            p["bytes"] = static_cast<long long>(content.size());
            p["sha256"] = sha;
            p["overwrote"] = existed;
            tracer_->emit("vault.write_text", p);
        }

        out["ok"] = true;
        out["path"] = fs::relative(rv.path, root_, ec).string();
        out["bytes"] = static_cast<long long>(content.size());
        out["sha256"] = sha;
        out["overwrote"] = existed;
        out["origin_signature"] = std::string("MrLiouWord");
        return out;
    }

    // ── mkdir ──
    Json mkdir(const std::string& rel) {
        Json out = Json::object();
        auto rv = resolve(rel, false);
        if (!rv.ok) { out["ok"] = false; out["error"] = rv.error; return out; }

        std::error_code ec;
        fs::create_directories(rv.path, ec);
        if (ec) { out["ok"] = false; out["error"] = ec.message(); return out; }

        if (tracer_) {
            Json p = Json::object();
            p["path"] = fs::relative(rv.path, root_, ec).string();
            tracer_->emit("vault.mkdir", p);
        }

        out["ok"] = true;
        out["path"] = fs::relative(rv.path, root_, ec).string();
        return out;
    }

    // ── info / stat ──
    Json info(const std::string& rel) const {
        Json out = Json::object();
        auto rv = resolve(rel, true);
        if (!rv.ok) { out["ok"] = false; out["error"] = rv.error; return out; }

        struct stat st{};
        if (::stat(rv.path.c_str(), &st) != 0) {
            out["ok"] = false; out["error"] = "stat_failed"; return out;
        }
        std::error_code ec;
        out["ok"] = true;
        out["path"] = fs::relative(rv.path, root_, ec).string();
        out["type"] = std::string(S_ISDIR(st.st_mode) ? "dir" : "file");
        out["size"] = static_cast<long long>(st.st_size);
        out["mtime"] = static_cast<long long>(st.st_mtime);
        out["mode"] = static_cast<long long>(st.st_mode & 0777);
        return out;
    }

private:
    bool within(const fs::path& p) const {
        auto a = p.string();
        auto r = root_.string();
        if (a.size() < r.size()) return false;
        if (a.compare(0, r.size(), r) != 0) return false;
        return a.size() == r.size() || a[r.size()] == '/';
    }

    fs::path root_;
    Tracer* tracer_;
};

}  // namespace mrl
