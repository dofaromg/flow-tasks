// mrliouai_core/src/main.cpp
// MrLiouAI Core Server — C++ 實作，取代 FireCore stub + Flask 空殼
// origin_signature: MrLiouWord
//
// 取代對象：
//   MRL_Mother/MRL_FireCore_v1_0/modules/mrl-firecore-auth/src/index.ts   (91 行 stub → 真實 JWT/PBKDF2)
//   MRL_Mother/MRL_FireCore_v1_0/modules/mrl-firecore-store/src/index.ts  (91 行 stub → 真實 CRUD)
//   apps/module-a/app.py                                                   (28 行 Flask 空殼)
//   apps/orchestrator/app.py                                               (61 行 Flask 空殼)
//
// 用法：
//   ./mrliouai_core --port 8800 --data ./data --vault ./vault --secret <jwt_secret>
//   環境變數：MRL_JWT_SECRET, MRL_HUMAN_TOKEN, MRL_PORT, MRL_DATA_DIR, MRL_VAULT_ROOT

#include <csignal>
#include <cstdlib>
#include <filesystem>
#include <iostream>
#include <string>

#include "mrl/auth.hpp"
#include "mrl/http.hpp"
#include "mrl/json.hpp"
#include "mrl/merkle.hpp"
#include "mrl/store.hpp"
#include "mrl/vault.hpp"

using namespace mrl;

namespace {

constexpr const char* VERSION = "1.0.0";
constexpr const char* ORIGIN = "MrLiouWord";

Server* g_server = nullptr;

void on_signal(int sig) {
    std::cerr << "\n[mrliouai_core] signal " << sig << " — graceful shutdown\n";
    if (g_server) g_server->stop();
    std::exit(0);
}

std::string env_or(const char* k, const std::string& def) {
    const char* v = std::getenv(k);
    return (v && *v) ? std::string(v) : def;
}

Json ok_envelope() {
    Json j = Json::object();
    j["ok"] = true;
    j["origin_signature"] = std::string(ORIGIN);
    return j;
}

Json err_envelope(const std::string& code) {
    Json j = Json::object();
    j["ok"] = false;
    j["error"] = code;
    j["origin_signature"] = std::string(ORIGIN);
    return j;
}

// 從 path 拆出 /v1/store/documents/<collection>/<doc_id>
bool split_two(const std::string& path, const std::string& prefix,
               std::string& a, std::string& b) {
    if (path.rfind(prefix, 0) != 0) return false;
    std::string rest = path.substr(prefix.size());
    while (!rest.empty() && rest.front() == '/') rest.erase(rest.begin());
    size_t s = rest.find('/');
    if (s == std::string::npos) { a = rest; b.clear(); return !a.empty(); }
    a = rest.substr(0, s);
    b = rest.substr(s + 1);
    while (!b.empty() && b.back() == '/') b.pop_back();
    return !a.empty();
}

}  // namespace

int main(int argc, char** argv) {
    std::string host = "0.0.0.0";
    uint16_t port = static_cast<uint16_t>(std::strtoul(env_or("MRL_PORT", "8800").c_str(), nullptr, 10));
    std::string data_dir = env_or("MRL_DATA_DIR", "./data");
    std::string vault_root = env_or("MRL_VAULT_ROOT", "./vault");
    std::string jwt_secret = env_or("MRL_JWT_SECRET", "");
    std::string human_token = env_or("MRL_HUMAN_TOKEN", "");

    for (int i = 1; i < argc; ++i) {
        std::string a = argv[i];
        auto next = [&]() -> std::string { return (i + 1 < argc) ? argv[++i] : ""; };
        if (a == "--port") port = static_cast<uint16_t>(std::strtoul(next().c_str(), nullptr, 10));
        else if (a == "--host") host = next();
        else if (a == "--data") data_dir = next();
        else if (a == "--vault") vault_root = next();
        else if (a == "--secret") jwt_secret = next();
        else if (a == "--token") human_token = next();
        else if (a == "--version") { std::cout << VERSION << "\n"; return 0; }
        else if (a == "--help") {
            std::cout << "mrliouai_core " << VERSION << " (origin_signature: " << ORIGIN << ")\n"
                      << "  --port N        listen port (default 8800)\n"
                      << "  --host ADDR     bind address (default 0.0.0.0)\n"
                      << "  --data DIR      data directory (default ./data)\n"
                      << "  --vault DIR     vault sandbox root (default ./vault)\n"
                      << "  --secret S      JWT HS256 secret (or MRL_JWT_SECRET)\n"
                      << "  --token T       human token for writes (or MRL_HUMAN_TOKEN)\n";
            return 0;
        }
    }

    std::error_code ec;
    std::filesystem::create_directories(data_dir, ec);
    std::filesystem::create_directories(vault_root, ec);

    if (jwt_secret.empty()) {
        jwt_secret = random_hex(32);
        std::cerr << "[mrliouai_core] WARNING: no MRL_JWT_SECRET set — generated ephemeral secret. "
                     "Tokens will not survive restart.\n";
    }

    Tracer tracer(data_dir + "/trace.jsonl", data_dir + "/trace.state.json");
    AuthService auth(data_dir, jwt_secret, &tracer);
    StoreService store(data_dir, &tracer);
    Vault vault(vault_root, &tracer);

    Server server;
    g_server = &server;
    std::signal(SIGINT, on_signal);
    std::signal(SIGTERM, on_signal);
    std::signal(SIGPIPE, SIG_IGN);

    // ─────────────── Health ───────────────
    server.get("/health", [&](const Request&) {
        Json j = ok_envelope();
        j["service"] = std::string("mrliouai_core");
        j["version"] = std::string(VERSION);
        j["runtime"] = std::string("C++17 / POSIX, zero external deps");
        j["replaces"] = std::string("mrl-firecore-auth, mrl-firecore-store, module-a, orchestrator");
        j["merkle_root"] = tracer.root();
        j["tick"] = static_cast<long long>(tracer.tick());
        j["users"] = static_cast<long long>(auth.user_count());
        j["active_refresh_tokens"] = static_cast<long long>(auth.active_refresh_count());
        j["documents"] = static_cast<long long>(store.count());
        j["vault_root"] = vault.root().string();

        Json eps = Json::array();
        for (const char* e : {"/health", "/v1/auth/signup", "/v1/auth/signin",
                              "/v1/auth/refresh", "/v1/auth/verify", "/v1/auth/revoke",
                              "/v1/store/documents", "/v1/store/query", "/v1/store/history",
                              "/v1/store/pending_sync",
                              "/vault/list", "/vault/read_text", "/vault/info",
                              "/vault/write_text", "/vault/mkdir",
                              "/trace/verify", "/trace/root"})
            eps.push(Json(std::string(e)));
        j["endpoints"] = eps;
        return Response::json(j);
    });

    // ─────────────── FireCore Auth（真實實作） ───────────────
    server.post("/v1/auth/signup", [&](const Request& req) {
        Json b = req.json();
        auto r = auth.signup(b.at("email").as_string(), b.at("password").as_string());
        if (!r.ok) {
            Json j = err_envelope(r.error);
            return Response::json(j, r.error == "email_already_registered" ? 409 : 400);
        }
        Json j = ok_envelope();
        j["user_id"] = r.user_id;
        j["password_algo"] = std::string("pbkdf2_sha256");
        j["iterations"] = static_cast<long long>(PBKDF2_ITERATIONS);
        return Response::json(j, 201);
    });

    server.post("/v1/auth/signin", [&](const Request& req) {
        Json b = req.json();
        auto r = auth.signin(b.at("email").as_string(), b.at("password").as_string());
        if (!r.ok) return Response::json(err_envelope(r.error), 401);

        Json j = ok_envelope();
        j["user_id"] = r.user_id;
        j["access_token"] = r.access_token;
        j["refresh_token"] = r.refresh_token;
        j["token_type"] = std::string("Bearer");
        j["expires_in"] = r.expires_in;
        j["alg"] = std::string("HS256");
        return Response::json(j);
    });

    server.post("/v1/auth/refresh", [&](const Request& req) {
        Json b = req.json();
        auto r = auth.refresh(b.at("refresh_token").as_string());
        if (!r.ok) return Response::json(err_envelope(r.error), 401);

        Json j = ok_envelope();
        j["user_id"] = r.user_id;
        j["access_token"] = r.access_token;
        j["refresh_token"] = r.refresh_token;  // 輪替後的新 token
        j["token_type"] = std::string("Bearer");
        j["expires_in"] = r.expires_in;
        j["rotated"] = true;
        return Response::json(j);
    });

    server.post("/v1/auth/revoke", [&](const Request& req) {
        Json b = req.json();
        bool ok = auth.revoke(b.at("refresh_token").as_string());
        if (!ok) return Response::json(err_envelope("refresh_token_unknown"), 404);
        Json j = ok_envelope();
        j["revoked"] = true;
        return Response::json(j);
    });

    auto verify_handler = [&](const Request& req) {
        std::string tok;
        std::string authz = req.header("authorization");
        if (authz.rfind("Bearer ", 0) == 0) tok = authz.substr(7);
        if (tok.empty()) tok = req.q("token");
        if (tok.empty()) tok = req.json().at("access_token").as_string();
        if (tok.empty()) return Response::json(err_envelope("no_token_provided"), 400);

        auto v = auth.verify(tok);
        if (!v.valid) {
            Json j = err_envelope("token_invalid");
            j["reason"] = v.reason;
            return Response::json(j, 401);
        }
        Json j = ok_envelope();
        j["valid"] = true;
        j["claims"] = v.payload;
        return Response::json(j);
    };
    server.post("/v1/auth/verify", verify_handler);
    server.get("/v1/auth/verify", verify_handler);

    // ─────────────── FireCore Store（真實實作） ───────────────
    server.post("/v1/store/query", [&](const Request& req) {
        Json b = req.json();
        auto r = store.query(b.at("collection").as_string(),
                             b.at("field").as_string(),
                             b.at("value").as_string(),
                             static_cast<size_t>(b.at("limit").as_int(50)),
                             b.at("cursor").as_string());
        Json docs = Json::array();
        for (const auto& d : r.docs) docs.push(d.to_json());

        Json j = ok_envelope();
        j["documents"] = docs;
        j["count"] = static_cast<long long>(r.docs.size());
        j["scanned"] = static_cast<long long>(r.scanned);
        j["list_complete"] = r.complete;
        if (!r.next_cursor.empty()) j["next_cursor"] = r.next_cursor;
        return Response::json(j);
    });

    server.get("/v1/store/pending_sync", [&](const Request&) {
        auto pend = store.pending_sync();
        Json docs = Json::array();
        for (const auto& d : pend) docs.push(d.to_json());
        Json j = ok_envelope();
        j["pending"] = docs;
        j["count"] = static_cast<long long>(pend.size());
        j["note"] = std::string("DL580 is authoritative; these await sync");
        return Response::json(j);
    });

    server.get("/v1/store/history", [&](const Request& req) {
        std::string coll = req.q("collection");
        std::string id = req.q("doc_id");
        if (coll.empty() || id.empty())
            return Response::json(err_envelope("collection_and_doc_id_required"), 400);

        auto hist = store.history(coll, id);
        Json arr = Json::array();
        for (const auto& h : hist) arr.push(h);
        Json j = ok_envelope();
        j["key"] = coll + "/" + id;
        j["versions"] = arr;
        j["count"] = static_cast<long long>(hist.size());
        return Response::json(j);
    });

    // POST /v1/store/documents            → create（body: collection, payload, doc_id?）
    // PUT  /v1/store/documents/<c>/<id>   → update（body: payload, expected_version?）
    // GET  /v1/store/documents/<c>/<id>   → get
    // DELETE /v1/store/documents/<c>/<id> → soft delete（不真刪）
    server.post("/v1/store/documents", [&](const Request& req) {
        Json b = req.json();
        auto r = store.create(b.at("collection").as_string(),
                              b.at("payload"),
                              b.at("doc_id").as_string());
        if (!r.ok) {
            Json j = err_envelope(r.error);
            if (!r.doc_id.empty()) { j["doc_id"] = r.doc_id; j["current_version"] = r.version; }
            return Response::json(j, r.http_status);
        }
        Json j = ok_envelope();
        j["doc_id"] = r.doc_id;
        j["version"] = r.version;
        return Response::json(j, 201);
    });

    server.get("/v1/store/documents", [&](const Request& req) {
        std::string coll, id;
        if (!split_two(req.path, "/v1/store/documents", coll, id) || id.empty())
            return Response::json(err_envelope("path_must_be_/v1/store/documents/<collection>/<doc_id>"), 400);

        auto r = store.get(coll, id);
        if (!r.ok) return Response::json(err_envelope(r.error), 404);
        Json j = ok_envelope();
        j["document"] = r.doc.to_json();
        return Response::json(j);
    });

    server.put("/v1/store/documents", [&](const Request& req) {
        std::string coll, id;
        if (!split_two(req.path, "/v1/store/documents", coll, id) || id.empty())
            return Response::json(err_envelope("path_must_be_/v1/store/documents/<collection>/<doc_id>"), 400);

        Json b = req.json();
        auto r = store.update(coll, id, b.at("payload"), b.at("expected_version").as_int(0));
        if (!r.ok) {
            Json j = err_envelope(r.error);
            if (r.version) j["current_version"] = r.version;
            return Response::json(j, r.http_status);
        }
        Json j = ok_envelope();
        j["doc_id"] = r.doc_id;
        j["version"] = r.version;
        return Response::json(j);
    });

    server.del("/v1/store/documents", [&](const Request& req) {
        std::string coll, id;
        if (!split_two(req.path, "/v1/store/documents", coll, id) || id.empty())
            return Response::json(err_envelope("path_must_be_/v1/store/documents/<collection>/<doc_id>"), 400);

        auto r = store.soft_delete(coll, id);
        if (!r.ok) return Response::json(err_envelope(r.error), r.http_status);
        Json j = ok_envelope();
        j["doc_id"] = r.doc_id;
        j["version"] = r.version;
        j["mode"] = std::string("soft_delete_only_data_retained");
        return Response::json(j);
    });

    // ─────────────── Vault（沙箱檔案系統） ───────────────
    server.get("/vault/list", [&](const Request& req) {
        Json r = vault.list(req.q("path", "."));
        return Response::json(r, r.at("ok").as_bool() ? 200 : 404);
    });

    server.get("/vault/read_text", [&](const Request& req) {
        Json r = vault.read_text(req.q("path"));
        return Response::json(r, r.at("ok").as_bool() ? 200 : 404);
    });

    server.get("/vault/info", [&](const Request& req) {
        Json r = vault.info(req.q("path"));
        return Response::json(r, r.at("ok").as_bool() ? 200 : 404);
    });

    // 寫入需要 human token（對應 flowcore_loop.py 的 X-Human-Token 保護）
    auto require_token = [&](const Request& req) -> bool {
        if (human_token.empty()) return true;  // 未設定則不強制
        return secure_equals(req.header("x-human-token"), human_token);
    };

    server.post("/vault/write_text", [&](const Request& req) {
        if (!require_token(req)) return Response::json(err_envelope("human_token_required"), 401);
        Json b = req.json();
        Json r = vault.write_text(b.at("path").as_string(), b.at("content").as_string());
        return Response::json(r, r.at("ok").as_bool() ? 200 : 400);
    });

    server.post("/vault/mkdir", [&](const Request& req) {
        if (!require_token(req)) return Response::json(err_envelope("human_token_required"), 401);
        Json b = req.json();
        Json r = vault.mkdir(b.at("path").as_string());
        return Response::json(r, r.at("ok").as_bool() ? 200 : 400);
    });

    // ─────────────── Merkle Trace ───────────────
    server.get("/trace/root", [&](const Request&) {
        Json j = ok_envelope();
        j["merkle_root"] = tracer.root();
        j["tick"] = static_cast<long long>(tracer.tick());
        return Response::json(j);
    });

    server.get("/trace/verify", [&](const Request&) {
        std::string err;
        bool ok = tracer.verify(&err);
        Json j = Json::object();
        j["ok"] = ok;
        j["chain_intact"] = ok;
        if (!ok) j["error"] = err;
        j["merkle_root"] = tracer.root();
        j["tick"] = static_cast<long long>(tracer.tick());
        j["origin_signature"] = std::string(ORIGIN);
        return Response::json(j, ok ? 200 : 409);
    });

    // ─────────────── Root ───────────────
    server.get("/", [&](const Request&) {
        Json j = ok_envelope();
        j["name"] = std::string("MrLiouAI Core");
        j["version"] = std::string(VERSION);
        j["philosophy"] = std::string("怎麼過去，就怎麼回來");
        j["law"] = std::string("不刪檔 — no destructive deletes in this runtime");
        return Response::json(j);
    });

    if (!server.listen(host, port)) {
        std::cerr << "[mrliouai_core] FATAL: cannot bind " << host << ":" << port << "\n";
        return 1;
    }

    Json boot = Json::object();
    boot["version"] = std::string(VERSION);
    boot["port"] = static_cast<long long>(port);
    boot["data_dir"] = data_dir;
    boot["vault_root"] = vault.root().string();
    tracer.emit("core.boot", boot);

    std::cout << "[mrliouai_core] " << VERSION << " listening on " << host << ":" << port << "\n"
              << "  data:  " << data_dir << "\n"
              << "  vault: " << vault.root().string() << "\n"
              << "  merkle_root: " << tracer.root().substr(0, 16) << "...\n"
              << "  origin_signature: " << ORIGIN << "\n";

    server.serve_forever();
    return 0;
}
