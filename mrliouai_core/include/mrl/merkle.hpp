// mrliouai_core/include/mrl/merkle.hpp
// Merkle 追蹤鏈 — append-only JSONL + SHA-256 鏈式根
// origin_signature: MrLiouWord
// 對應規格：MRL_Mother/04_runtime/flowcontainer.py Tracer 類別
//           MRL_Mother/04_runtime/flowcore_loop.py Merkle Tracer
// 規則：merkle_root = SHA256(prev_root + event_hash)，原子寫入，防篡改
#pragma once

#include <chrono>
#include <cstdio>
#include <fstream>
#include <mutex>
#include <string>

#include "json.hpp"
#include "sha256.hpp"

namespace mrl {

inline std::string now_iso() {
    auto now = std::chrono::system_clock::now();
    auto t = std::chrono::system_clock::to_time_t(now);
    auto us = std::chrono::duration_cast<std::chrono::microseconds>(
                  now.time_since_epoch()) % 1000000;
    std::tm tm{};
    gmtime_r(&t, &tm);
    char buf[64];
    std::snprintf(buf, sizeof(buf), "%04d-%02d-%02dT%02d:%02d:%02d.%06lldZ",
                  tm.tm_year + 1900, tm.tm_mon + 1, tm.tm_mday,
                  tm.tm_hour, tm.tm_min, tm.tm_sec,
                  static_cast<long long>(us.count()));
    return buf;
}

inline long long now_epoch_sec() {
    return std::chrono::duration_cast<std::chrono::seconds>(
               std::chrono::system_clock::now().time_since_epoch()).count();
}

class Tracer {
public:
    explicit Tracer(std::string trace_path, std::string state_path = "")
        : trace_path_(std::move(trace_path)),
          state_path_(state_path.empty() ? trace_path_ + ".state.json" : std::move(state_path)) {
        load_state();
    }

    // 附加事件到鏈上，回傳新的 merkle_root
    std::string emit(const std::string& event, Json payload = Json::object()) {
        std::lock_guard<std::mutex> lk(mu_);

        ++tick_;
        Json rec = Json::object();
        rec["tick"] = static_cast<long long>(tick_);
        rec["ts"] = now_iso();
        rec["event"] = event;
        rec["payload"] = std::move(payload);
        rec["prev_root"] = root_;
        rec["origin_signature"] = std::string("MrLiouWord");

        std::string body = rec.dump();
        std::string event_hash = SHA256::hex(body);
        root_ = SHA256::hex(root_ + event_hash);

        rec["event_hash"] = event_hash;
        rec["merkle_root"] = root_;

        // append-only JSONL
        std::ofstream f(trace_path_, std::ios::app);
        if (f) {
            f << rec.dump() << "\n";
            f.flush();
        }

        save_state();
        return root_;
    }

    std::string root() const {
        std::lock_guard<std::mutex> lk(mu_);
        return root_;
    }

    uint64_t tick() const {
        std::lock_guard<std::mutex> lk(mu_);
        return tick_;
    }

    // 驗證整條鏈的完整性 — 重算每一步的 root
    bool verify(std::string* err = nullptr) const {
        std::ifstream f(trace_path_);
        if (!f) {
            if (err) *err = "trace file not readable: " + trace_path_;
            return false;
        }
        std::string line, expect_root;
        uint64_t expect_tick = 0;
        while (std::getline(f, line)) {
            if (line.empty()) continue;
            Json rec = Json::parse(line);
            ++expect_tick;

            if (static_cast<uint64_t>(rec.at("tick").as_int()) != expect_tick) {
                if (err) *err = "tick gap at " + std::to_string(expect_tick);
                return false;
            }
            if (rec.at("prev_root").as_string() != expect_root) {
                if (err) *err = "prev_root mismatch at tick " + std::to_string(expect_tick);
                return false;
            }

            // 重建 body（不含 event_hash / merkle_root）
            Json body = Json::object();
            body["tick"] = rec.at("tick").as_int();
            body["ts"] = rec.at("ts").as_string();
            body["event"] = rec.at("event").as_string();
            body["payload"] = rec.at("payload");
            body["prev_root"] = rec.at("prev_root").as_string();
            body["origin_signature"] = rec.at("origin_signature").as_string();

            std::string h = SHA256::hex(body.dump());
            if (h != rec.at("event_hash").as_string()) {
                if (err) *err = "event_hash tampered at tick " + std::to_string(expect_tick);
                return false;
            }

            std::string r = SHA256::hex(expect_root + h);
            if (r != rec.at("merkle_root").as_string()) {
                if (err) *err = "merkle_root broken at tick " + std::to_string(expect_tick);
                return false;
            }
            expect_root = r;
        }
        return true;
    }

private:
    void load_state() {
        std::ifstream f(state_path_);
        if (!f) return;
        std::string body((std::istreambuf_iterator<char>(f)),
                         std::istreambuf_iterator<char>());
        if (body.empty()) return;
        Json j = Json::parse(body);
        root_ = j.at("merkle_root").as_string();
        tick_ = static_cast<uint64_t>(j.at("tick").as_int());
    }

    // 原子寫入：先寫 .tmp 再 rename（對應 flowcore_loop.py 的 os.replace）
    void save_state() const {
        Json j = Json::object();
        j["merkle_root"] = root_;
        j["tick"] = static_cast<long long>(tick_);
        j["updated"] = now_iso();
        j["origin_signature"] = std::string("MrLiouWord");

        std::string tmp = state_path_ + ".tmp";
        {
            std::ofstream f(tmp, std::ios::trunc);
            if (!f) return;
            f << j.dump(2) << "\n";
            f.flush();
        }
        std::rename(tmp.c_str(), state_path_.c_str());
    }

    mutable std::mutex mu_;
    std::string trace_path_;
    std::string state_path_;
    std::string root_;      // 空字串 = 創世狀態
    uint64_t tick_ = 0;
};

}  // namespace mrl
