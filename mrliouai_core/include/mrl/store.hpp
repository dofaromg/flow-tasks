// mrliouai_core/include/mrl/store.hpp
// FireCore Store — 真實實作，取代 mrl-firecore-store 的 202 stub
// origin_signature: MrLiouWord
//
// 原 stub 行為（MRL_Mother/MRL_FireCore_v1_0/modules/mrl-firecore-store/src/index.ts:40-49）：
//   storeContract() → 回 202 {accepted:false, reason:"authoritative write requires DL580"}
//   零 CRUD、零查詢、零 D1 互動
//
// 本檔實作：
//   - 文件 CRUD（collection/document 模型）
//   - 樂觀鎖版本控制（version 遞增，衝突回 409）
//   - 版本歷史（對應 mrl_fc_document_versions）
//   - 查詢：collection 前綴 + 欄位等值 + 分頁 cursor
//   - 原子持久化 + DL580 同步狀態欄位
#pragma once

#include <algorithm>
#include <fstream>
#include <map>
#include <mutex>
#include <string>
#include <vector>

#include "json.hpp"
#include "merkle.hpp"
#include "sha256.hpp"

namespace mrl {

// 對應 SQL schema mrl_fc_documents
struct Document {
    std::string doc_id;
    std::string collection;
    Json payload = Json::object();
    long long version = 0;
    std::string created_at;
    std::string updated_at;
    std::string dl580_sync_state = "pending";  // pending | synced | conflict
    bool deleted = false;

    Json to_json() const {
        Json j = Json::object();
        j["doc_id"] = doc_id;
        j["collection"] = collection;
        j["payload"] = payload;
        j["version"] = version;
        j["created_at"] = created_at;
        j["updated_at"] = updated_at;
        j["dl580_sync_state"] = dl580_sync_state;
        j["deleted"] = deleted;
        return j;
    }

    static Document from_json(const Json& j) {
        Document d;
        d.doc_id = j.at("doc_id").as_string();
        d.collection = j.at("collection").as_string();
        d.payload = j.at("payload");
        d.version = j.at("version").as_int();
        d.created_at = j.at("created_at").as_string();
        d.updated_at = j.at("updated_at").as_string();
        d.dl580_sync_state = j.at("dl580_sync_state").as_string("pending");
        d.deleted = j.at("deleted").as_bool();
        return d;
    }
};

class StoreService {
public:
    StoreService(std::string data_dir, Tracer* tracer = nullptr)
        : dir_(std::move(data_dir)), tracer_(tracer) {
        load();
    }

    struct WriteResult {
        bool ok = false;
        std::string error;
        std::string doc_id;
        long long version = 0;
        int http_status = 200;
    };

    // 建立文件。doc_id 空 → 自動產生
    WriteResult create(const std::string& collection, const Json& payload,
                       std::string doc_id = "") {
        std::lock_guard<std::mutex> lk(mu_);
        WriteResult r;

        if (collection.empty()) {
            r.error = "collection_required";
            r.http_status = 400;
            return r;
        }
        if (doc_id.empty()) doc_id = "doc_" + random_id();

        std::string key = collection + "/" + doc_id;
        auto it = docs_.find(key);
        if (it != docs_.end() && !it->second.deleted) {
            r.error = "document_already_exists";
            r.http_status = 409;
            r.doc_id = doc_id;
            r.version = it->second.version;
            return r;
        }

        Document d;
        d.doc_id = doc_id;
        d.collection = collection;
        d.payload = payload;
        d.version = 1;
        d.created_at = now_iso();
        d.updated_at = d.created_at;
        d.dl580_sync_state = "pending";

        docs_[key] = d;
        append_version(d, "create");
        persist();
        trace("store.create", key, d.version);

        r.ok = true;
        r.doc_id = doc_id;
        r.version = 1;
        r.http_status = 201;
        return r;
    }

    // 更新文件。expected_version > 0 時做樂觀鎖檢查
    WriteResult update(const std::string& collection, const std::string& doc_id,
                       const Json& payload, long long expected_version = 0) {
        std::lock_guard<std::mutex> lk(mu_);
        WriteResult r;
        std::string key = collection + "/" + doc_id;

        auto it = docs_.find(key);
        if (it == docs_.end() || it->second.deleted) {
            r.error = "document_not_found";
            r.http_status = 404;
            return r;
        }

        Document& d = it->second;
        if (expected_version > 0 && d.version != expected_version) {
            r.error = "version_conflict";
            r.http_status = 409;
            r.doc_id = doc_id;
            r.version = d.version;  // 回傳當前版本讓 client 重試
            return r;
        }

        d.payload = payload;
        ++d.version;
        d.updated_at = now_iso();
        d.dl580_sync_state = "pending";

        append_version(d, "update");
        persist();
        trace("store.update", key, d.version);

        r.ok = true;
        r.doc_id = doc_id;
        r.version = d.version;
        return r;
    }

    struct ReadResult {
        bool ok = false;
        std::string error;
        Document doc;
    };

    ReadResult get(const std::string& collection, const std::string& doc_id) const {
        std::lock_guard<std::mutex> lk(mu_);
        ReadResult r;
        auto it = docs_.find(collection + "/" + doc_id);
        if (it == docs_.end() || it->second.deleted) {
            r.error = "document_not_found";
            return r;
        }
        r.ok = true;
        r.doc = it->second;
        return r;
    }

    // 軟刪除 — 保留資料，只標記 deleted（不真的移除，符合不刪檔法則）
    WriteResult soft_delete(const std::string& collection, const std::string& doc_id) {
        std::lock_guard<std::mutex> lk(mu_);
        WriteResult r;
        std::string key = collection + "/" + doc_id;
        auto it = docs_.find(key);
        if (it == docs_.end() || it->second.deleted) {
            r.error = "document_not_found";
            r.http_status = 404;
            return r;
        }
        Document& d = it->second;
        d.deleted = true;
        ++d.version;
        d.updated_at = now_iso();
        d.dl580_sync_state = "pending";

        append_version(d, "soft_delete");
        persist();
        trace("store.soft_delete", key, d.version);

        r.ok = true;
        r.doc_id = doc_id;
        r.version = d.version;
        return r;
    }

    struct QueryResult {
        std::vector<Document> docs;
        std::string next_cursor;
        bool complete = true;
        size_t scanned = 0;
    };

    // 查詢：collection 過濾 + 欄位等值過濾 + cursor 分頁
    QueryResult query(const std::string& collection,
                      const std::string& field = "",
                      const std::string& value = "",
                      size_t limit = 50,
                      const std::string& cursor = "") const {
        std::lock_guard<std::mutex> lk(mu_);
        QueryResult r;
        if (limit == 0 || limit > 500) limit = 50;

        for (const auto& kv : docs_) {
            const Document& d = kv.second;
            if (d.deleted) continue;
            if (!collection.empty() && d.collection != collection) continue;
            if (!cursor.empty() && kv.first <= cursor) continue;
            ++r.scanned;

            if (!field.empty()) {
                const Json& f = d.payload.at(field);
                std::string got;
                if (f.is_string()) got = f.as_string();
                else if (f.is_number()) got = std::to_string(f.as_int());
                else if (f.is_bool()) got = f.as_bool() ? "true" : "false";
                if (got != value) continue;
            }

            if (r.docs.size() >= limit) {
                r.complete = false;
                r.next_cursor = kv.first;
                break;
            }
            r.docs.push_back(d);
        }
        return r;
    }

    // 版本歷史
    std::vector<Json> history(const std::string& collection,
                              const std::string& doc_id) const {
        std::vector<Json> out;
        std::ifstream f(dir_ + "/doc_versions.jsonl");
        std::string line;
        std::string key = collection + "/" + doc_id;
        while (f && std::getline(f, line)) {
            if (line.empty()) continue;
            Json j = Json::parse(line);
            if (j.at("key").as_string() == key) out.push_back(j);
        }
        return out;
    }

    size_t count() const {
        std::lock_guard<std::mutex> lk(mu_);
        size_t n = 0;
        for (const auto& kv : docs_) if (!kv.second.deleted) ++n;
        return n;
    }

    // DL580 同步標記
    bool mark_synced(const std::string& collection, const std::string& doc_id) {
        std::lock_guard<std::mutex> lk(mu_);
        auto it = docs_.find(collection + "/" + doc_id);
        if (it == docs_.end()) return false;
        it->second.dl580_sync_state = "synced";
        persist();
        return true;
    }

    std::vector<Document> pending_sync() const {
        std::lock_guard<std::mutex> lk(mu_);
        std::vector<Document> out;
        for (const auto& kv : docs_)
            if (kv.second.dl580_sync_state == "pending") out.push_back(kv.second);
        return out;
    }

private:
    static std::string random_id() {
        std::ifstream f("/dev/urandom", std::ios::binary);
        std::vector<uint8_t> buf(12);
        if (f) f.read(reinterpret_cast<char*>(buf.data()), 12);
        return to_hex(buf);
    }

    void append_version(const Document& d, const std::string& op) const {
        std::ofstream f(dir_ + "/doc_versions.jsonl", std::ios::app);
        if (!f) return;
        Json j = Json::object();
        j["key"] = d.collection + "/" + d.doc_id;
        j["op"] = op;
        j["version"] = d.version;
        j["ts"] = now_iso();
        j["payload"] = d.payload;
        j["payload_sha256"] = SHA256::hex(d.payload.dump());
        j["origin_signature"] = std::string("MrLiouWord");
        f << j.dump() << "\n";
    }

    void trace(const std::string& ev, const std::string& key, long long ver) {
        if (!tracer_) return;
        Json p = Json::object();
        p["key"] = key;
        p["version"] = ver;
        tracer_->emit(ev, p);
    }

    void persist() const {
        std::string tmp = dir_ + "/documents.jsonl.tmp";
        {
            std::ofstream f(tmp, std::ios::trunc);
            if (!f) return;
            for (const auto& kv : docs_) f << kv.second.to_json().dump() << "\n";
        }
        std::rename(tmp.c_str(), (dir_ + "/documents.jsonl").c_str());
    }

    void load() {
        std::ifstream f(dir_ + "/documents.jsonl");
        std::string line;
        while (f && std::getline(f, line)) {
            if (line.empty()) continue;
            Document d = Document::from_json(Json::parse(line));
            if (d.doc_id.empty()) continue;
            docs_[d.collection + "/" + d.doc_id] = d;
        }
    }

    mutable std::mutex mu_;
    std::string dir_;
    Tracer* tracer_;
    std::map<std::string, Document> docs_;  // key = collection/doc_id
};

}  // namespace mrl
