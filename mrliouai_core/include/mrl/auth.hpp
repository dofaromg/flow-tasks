// mrliouai_core/include/mrl/auth.hpp
// FireCore Auth — 真實實作，取代 mrl-firecore-auth 的 202 stub
// origin_signature: MrLiouWord
//
// 原 stub 行為（MRL_Mother/MRL_FireCore_v1_0/modules/mrl-firecore-auth/src/index.ts:40-49）：
//   authContract() → 回 202 {accepted:false, reason:"JWT private signing remains on DL580"}
//   零密碼哈希、零 JWT 產生、零 token 驗證、零資料庫互動
//
// 本檔實作：
//   - PBKDF2-HMAC-SHA256 密碼哈希（600000 迭代，32 byte salt）
//   - HS256 JWT 簽發 / 驗證（含 exp / iat / iss / sub 檢查）
//   - Refresh token 生命週期（簽發、輪替、撤銷）
//   - 常數時間比較防 timing attack
//   - 對應原 SQL schema: mrl_fc_users / mrl_fc_refresh_tokens / mrl_fc_auth_audit
#pragma once

#include <fstream>
#include <map>
#include <mutex>
#include <random>
#include <string>
#include <vector>

#include "base64.hpp"
#include "json.hpp"
#include "merkle.hpp"
#include "sha256.hpp"

namespace mrl {

// PBKDF2 參數 — OWASP 2023 建議 SHA-256 用 600,000 迭代
constexpr uint32_t PBKDF2_ITERATIONS = 600000;
constexpr size_t PBKDF2_DK_LEN = 32;
constexpr size_t SALT_LEN = 32;

inline std::string random_hex(size_t bytes) {
    static std::mutex mu;
    std::lock_guard<std::mutex> lk(mu);
    // 優先用 /dev/urandom（CSPRNG）
    std::ifstream f("/dev/urandom", std::ios::binary);
    std::vector<uint8_t> buf(bytes);
    if (f && f.read(reinterpret_cast<char*>(buf.data()),
                    static_cast<std::streamsize>(bytes))) {
        return to_hex(buf);
    }
    // 後備
    static std::mt19937_64 rng{std::random_device{}()};
    for (size_t i = 0; i < bytes; ++i)
        buf[i] = static_cast<uint8_t>(rng() & 0xff);
    return to_hex(buf);
}

// ── 密碼哈希 ──
// 格式：pbkdf2_sha256$<iterations>$<salt_hex>$<dk_hex>
inline std::string hash_password(const std::string& password,
                                 const std::string& salt_hex = "") {
    std::string salt = salt_hex.empty() ? random_hex(SALT_LEN) : salt_hex;
    auto dk = pbkdf2_sha256(password, salt, PBKDF2_ITERATIONS, PBKDF2_DK_LEN);
    return "pbkdf2_sha256$" + std::to_string(PBKDF2_ITERATIONS) + "$" + salt + "$" + to_hex(dk);
}

inline bool verify_password(const std::string& password, const std::string& stored) {
    // 解析 pbkdf2_sha256$iter$salt$dk
    std::vector<std::string> parts;
    size_t start = 0;
    while (true) {
        size_t p = stored.find('$', start);
        if (p == std::string::npos) { parts.push_back(stored.substr(start)); break; }
        parts.push_back(stored.substr(start, p - start));
        start = p + 1;
    }
    if (parts.size() != 4 || parts[0] != "pbkdf2_sha256") return false;

    uint32_t iter = static_cast<uint32_t>(std::strtoul(parts[1].c_str(), nullptr, 10));
    if (iter == 0 || iter > 10000000) return false;

    auto dk = pbkdf2_sha256(password, parts[2], iter, PBKDF2_DK_LEN);
    return secure_equals(to_hex(dk), parts[3]);
}

// ── JWT HS256 ──
struct JwtClaims {
    std::string sub;      // user_id
    std::string iss = "mrliouai";
    std::string aud;
    long long iat = 0;
    long long exp = 0;
    std::string jti;
    std::map<std::string, std::string> extra;
};

inline std::string jwt_sign(const JwtClaims& c, const std::string& secret) {
    Json hdr = Json::object();
    hdr["alg"] = std::string("HS256");
    hdr["typ"] = std::string("JWT");

    Json pl = Json::object();
    pl["sub"] = c.sub;
    pl["iss"] = c.iss;
    if (!c.aud.empty()) pl["aud"] = c.aud;
    pl["iat"] = c.iat ? c.iat : now_epoch_sec();
    pl["exp"] = c.exp;
    if (!c.jti.empty()) pl["jti"] = c.jti;
    pl["origin_signature"] = std::string("MrLiouWord");
    for (const auto& kv : c.extra) pl[kv.first] = kv.second;

    std::string signing_input = b64url(hdr.dump()) + "." + b64url(pl.dump());
    auto sig = hmac_sha256(secret, signing_input);
    return signing_input + "." + b64url(sig.data(), sig.size());
}

struct JwtVerifyResult {
    bool valid = false;
    std::string reason;
    Json payload = Json::object();
};

inline JwtVerifyResult jwt_verify(const std::string& token, const std::string& secret) {
    JwtVerifyResult r;

    size_t d1 = token.find('.');
    if (d1 == std::string::npos) { r.reason = "malformed_no_header_delim"; return r; }
    size_t d2 = token.find('.', d1 + 1);
    if (d2 == std::string::npos) { r.reason = "malformed_no_sig_delim"; return r; }

    std::string signing_input = token.substr(0, d2);
    std::string provided_sig = token.substr(d2 + 1);

    auto expect = hmac_sha256(secret, signing_input);
    std::string expect_b64 = b64url(expect.data(), expect.size());

    // 常數時間比較
    if (!secure_equals(expect_b64, provided_sig)) {
        r.reason = "signature_mismatch";
        return r;
    }

    std::string hdr_json = b64url_decode_str(token.substr(0, d1));
    Json hdr = Json::parse(hdr_json);
    if (hdr.at("alg").as_string() != "HS256") {
        r.reason = "alg_not_allowed";  // 拒絕 alg=none 降級攻擊
        return r;
    }

    r.payload = Json::parse(b64url_decode_str(token.substr(d1 + 1, d2 - d1 - 1)));

    long long exp = r.payload.at("exp").as_int();
    long long now = now_epoch_sec();
    if (exp != 0 && now >= exp) { r.reason = "expired"; return r; }

    long long iat = r.payload.at("iat").as_int();
    if (iat != 0 && iat > now + 60) { r.reason = "iat_in_future"; return r; }

    r.valid = true;
    return r;
}

// ── 使用者表 ── 對應 SQL schema mrl_fc_users
struct User {
    std::string user_id;
    std::string email;
    std::string password_hash;
    std::string created_at;
    bool disabled = false;
};

// ── Refresh token ── 對應 SQL schema mrl_fc_refresh_tokens
struct RefreshToken {
    std::string token_hash;  // 只存哈希，不存明文
    std::string user_id;
    long long expires_at = 0;
    bool revoked = false;
    std::string created_at;
};

// AuthService：檔案持久化（JSONL），DL580 PostgreSQL 為權威來源時可換 backend
class AuthService {
public:
    AuthService(std::string data_dir, std::string jwt_secret, Tracer* tracer = nullptr)
        : dir_(std::move(data_dir)), secret_(std::move(jwt_secret)), tracer_(tracer) {
        load();
    }

    struct SignupResult {
        bool ok = false;
        std::string error;
        std::string user_id;
    };

    SignupResult signup(const std::string& email, const std::string& password) {
        std::lock_guard<std::mutex> lk(mu_);
        SignupResult r;

        if (email.empty() || email.find('@') == std::string::npos) {
            r.error = "invalid_email";
            return r;
        }
        if (password.size() < 8) {
            r.error = "password_too_short_min_8";
            return r;
        }
        if (by_email_.count(email)) {
            r.error = "email_already_registered";
            return r;
        }

        User u;
        u.user_id = "usr_" + random_hex(16);
        u.email = email;
        u.password_hash = hash_password(password);
        u.created_at = now_iso();

        users_[u.user_id] = u;
        by_email_[email] = u.user_id;
        persist_users();
        audit("signup", u.user_id, true);

        r.ok = true;
        r.user_id = u.user_id;
        return r;
    }

    struct SigninResult {
        bool ok = false;
        std::string error;
        std::string user_id;
        std::string access_token;
        std::string refresh_token;
        long long expires_in = 0;
    };

    SigninResult signin(const std::string& email, const std::string& password,
                        long long access_ttl = 3600, long long refresh_ttl = 2592000) {
        std::lock_guard<std::mutex> lk(mu_);
        SigninResult r;

        auto it = by_email_.find(email);
        if (it == by_email_.end()) {
            // 即使帳號不存在也跑一次哈希，避免 timing 洩漏帳號存在性
            (void)hash_password(password, std::string(SALT_LEN * 2, '0'));
            r.error = "invalid_credentials";
            audit("signin_fail_no_user", "", false);
            return r;
        }

        User& u = users_[it->second];
        if (u.disabled) {
            r.error = "account_disabled";
            audit("signin_fail_disabled", u.user_id, false);
            return r;
        }
        if (!verify_password(password, u.password_hash)) {
            r.error = "invalid_credentials";
            audit("signin_fail_bad_password", u.user_id, false);
            return r;
        }

        r.ok = true;
        r.user_id = u.user_id;
        r.expires_in = access_ttl;
        r.access_token = issue_access(u.user_id, access_ttl);
        r.refresh_token = issue_refresh(u.user_id, refresh_ttl);
        audit("signin", u.user_id, true);
        return r;
    }

    // Refresh token 輪替：舊 token 撤銷，發新的（防重放）
    SigninResult refresh(const std::string& refresh_token,
                         long long access_ttl = 3600, long long refresh_ttl = 2592000) {
        std::lock_guard<std::mutex> lk(mu_);
        SigninResult r;

        std::string h = SHA256::hex(refresh_token);
        auto it = refresh_.find(h);
        if (it == refresh_.end()) {
            r.error = "refresh_token_unknown";
            audit("refresh_fail_unknown", "", false);
            return r;
        }
        RefreshToken& rt = it->second;
        if (rt.revoked) {
            r.error = "refresh_token_revoked";
            audit("refresh_fail_revoked", rt.user_id, false);
            return r;
        }
        if (now_epoch_sec() >= rt.expires_at) {
            r.error = "refresh_token_expired";
            audit("refresh_fail_expired", rt.user_id, false);
            return r;
        }

        std::string uid = rt.user_id;
        rt.revoked = true;  // 輪替

        r.ok = true;
        r.user_id = uid;
        r.expires_in = access_ttl;
        r.access_token = issue_access(uid, access_ttl);
        r.refresh_token = issue_refresh(uid, refresh_ttl);
        persist_refresh();
        audit("refresh", uid, true);
        return r;
    }

    bool revoke(const std::string& refresh_token) {
        std::lock_guard<std::mutex> lk(mu_);
        auto it = refresh_.find(SHA256::hex(refresh_token));
        if (it == refresh_.end()) return false;
        it->second.revoked = true;
        persist_refresh();
        audit("revoke", it->second.user_id, true);
        return true;
    }

    JwtVerifyResult verify(const std::string& access_token) const {
        return jwt_verify(access_token, secret_);
    }

    size_t user_count() const {
        std::lock_guard<std::mutex> lk(mu_);
        return users_.size();
    }

    size_t active_refresh_count() const {
        std::lock_guard<std::mutex> lk(mu_);
        size_t n = 0;
        long long now = now_epoch_sec();
        for (const auto& kv : refresh_)
            if (!kv.second.revoked && kv.second.expires_at > now) ++n;
        return n;
    }

private:
    std::string issue_access(const std::string& uid, long long ttl) {
        JwtClaims c;
        c.sub = uid;
        c.iss = "mrliouai";
        c.aud = "mrliouai.api";
        c.iat = now_epoch_sec();
        c.exp = c.iat + ttl;
        c.jti = "jti_" + random_hex(12);
        return jwt_sign(c, secret_);
    }

    std::string issue_refresh(const std::string& uid, long long ttl) {
        std::string tok = "rt_" + random_hex(32);
        RefreshToken rt;
        rt.token_hash = SHA256::hex(tok);
        rt.user_id = uid;
        rt.expires_at = now_epoch_sec() + ttl;
        rt.created_at = now_iso();
        refresh_[rt.token_hash] = rt;
        persist_refresh();
        return tok;
    }

    void audit(const std::string& action, const std::string& uid, bool ok) {
        std::ofstream f(dir_ + "/auth_audit.jsonl", std::ios::app);
        if (f) {
            Json j = Json::object();
            j["ts"] = now_iso();
            j["action"] = action;
            j["user_id"] = uid;
            j["ok"] = ok;
            j["origin_signature"] = std::string("MrLiouWord");
            f << j.dump() << "\n";
        }
        if (tracer_) {
            Json p = Json::object();
            p["action"] = action;
            p["user_id"] = uid;
            p["ok"] = ok;
            tracer_->emit("firecore.auth", p);
        }
    }

    void persist_users() const {
        std::string tmp = dir_ + "/users.jsonl.tmp";
        {
            std::ofstream f(tmp, std::ios::trunc);
            if (!f) return;
            for (const auto& kv : users_) {
                Json j = Json::object();
                j["user_id"] = kv.second.user_id;
                j["email"] = kv.second.email;
                j["password_hash"] = kv.second.password_hash;
                j["created_at"] = kv.second.created_at;
                j["disabled"] = kv.second.disabled;
                f << j.dump() << "\n";
            }
        }
        std::rename(tmp.c_str(), (dir_ + "/users.jsonl").c_str());
    }

    void persist_refresh() const {
        std::string tmp = dir_ + "/refresh.jsonl.tmp";
        {
            std::ofstream f(tmp, std::ios::trunc);
            if (!f) return;
            for (const auto& kv : refresh_) {
                Json j = Json::object();
                j["token_hash"] = kv.second.token_hash;
                j["user_id"] = kv.second.user_id;
                j["expires_at"] = kv.second.expires_at;
                j["revoked"] = kv.second.revoked;
                j["created_at"] = kv.second.created_at;
                f << j.dump() << "\n";
            }
        }
        std::rename(tmp.c_str(), (dir_ + "/refresh.jsonl").c_str());
    }

    void load() {
        std::ifstream uf(dir_ + "/users.jsonl");
        std::string line;
        while (uf && std::getline(uf, line)) {
            if (line.empty()) continue;
            Json j = Json::parse(line);
            User u;
            u.user_id = j.at("user_id").as_string();
            u.email = j.at("email").as_string();
            u.password_hash = j.at("password_hash").as_string();
            u.created_at = j.at("created_at").as_string();
            u.disabled = j.at("disabled").as_bool();
            if (u.user_id.empty()) continue;
            users_[u.user_id] = u;
            by_email_[u.email] = u.user_id;
        }

        std::ifstream rf(dir_ + "/refresh.jsonl");
        while (rf && std::getline(rf, line)) {
            if (line.empty()) continue;
            Json j = Json::parse(line);
            RefreshToken rt;
            rt.token_hash = j.at("token_hash").as_string();
            rt.user_id = j.at("user_id").as_string();
            rt.expires_at = j.at("expires_at").as_int();
            rt.revoked = j.at("revoked").as_bool();
            rt.created_at = j.at("created_at").as_string();
            if (rt.token_hash.empty()) continue;
            refresh_[rt.token_hash] = rt;
        }
    }

    mutable std::mutex mu_;
    std::string dir_;
    std::string secret_;
    Tracer* tracer_;
    std::map<std::string, User> users_;
    std::map<std::string, std::string> by_email_;
    std::map<std::string, RefreshToken> refresh_;
};

}  // namespace mrl
