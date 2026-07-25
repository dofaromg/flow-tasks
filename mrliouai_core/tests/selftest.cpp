// mrliouai_core/tests/selftest.cpp
// 自我測試 — 驗證每個元件真的能跑，不是 stub
// origin_signature: MrLiouWord
// 建構執行： make test

#include <cassert>
#include <cstdlib>
#include <filesystem>
#include <iostream>
#include <string>

#include "mrl/auth.hpp"
#include "mrl/base64.hpp"
#include "mrl/json.hpp"
#include "mrl/merkle.hpp"
#include "mrl/sha256.hpp"
#include "mrl/store.hpp"
#include "mrl/vault.hpp"

using namespace mrl;

static int g_pass = 0;
static int g_fail = 0;

#define CHECK(cond, label)                                              \
    do {                                                                \
        if (cond) {                                                     \
            ++g_pass;                                                   \
            std::cout << "  PASS  " << (label) << "\n";                  \
        } else {                                                        \
            ++g_fail;                                                   \
            std::cout << "  FAIL  " << (label)                          \
                      << "   (" << __FILE__ << ":" << __LINE__ << ")\n"; \
        }                                                               \
    } while (0)

#define CHECK_EQ(got, want, label)                                      \
    do {                                                                \
        auto g_ = (got);                                                \
        auto w_ = (want);                                               \
        if (g_ == w_) {                                                 \
            ++g_pass;                                                   \
            std::cout << "  PASS  " << (label) << "\n";                  \
        } else {                                                        \
            ++g_fail;                                                   \
            std::cout << "  FAIL  " << (label) << "\n"                   \
                      << "        got  = " << g_ << "\n"                 \
                      << "        want = " << w_ << "\n";                \
        }                                                               \
    } while (0)

// ── SHA-256 官方測試向量 (NIST FIPS 180-4) ──
static void test_sha256() {
    std::cout << "\n[SHA-256] NIST 測試向量\n";
    CHECK_EQ(SHA256::hex(""),
             "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
             "empty string");
    CHECK_EQ(SHA256::hex("abc"),
             "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
             "\"abc\"");
    CHECK_EQ(SHA256::hex("abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq"),
             "248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1",
             "448-bit message");
    // 多 block（1,000,000 個 'a'）
    SHA256 s;
    std::string a(1000, 'a');
    for (int i = 0; i < 1000; ++i) s.update(a);
    CHECK_EQ(SHA256::to_hex(s.digest()),
             "cdc76e5c9914fb9281a1c7e284d73e67f1809a48a497200e046d39ccc7112cd0",
             "1,000,000 x 'a'");
}

// ── HMAC-SHA256 官方測試向量 (RFC 4231) ──
static void test_hmac() {
    std::cout << "\n[HMAC-SHA256] RFC 4231 測試向量\n";
    std::string key(20, '\x0b');
    auto d = hmac_sha256(key, "Hi There");
    CHECK_EQ(SHA256::to_hex(d),
             "b0344c61d8db38535ca8afceaf0bf12b881dc200c9833da726e9376c2e32cff7",
             "RFC 4231 Case 1");

    auto d2 = hmac_sha256("Jefe", "what do ya want for nothing?");
    CHECK_EQ(SHA256::to_hex(d2),
             "5bdcc146bf60754e6a042426089575c75a003f089d2739839dec58b964ec3843",
             "RFC 4231 Case 2");
}

// ── PBKDF2-HMAC-SHA256 官方測試向量 (RFC 6070 風格) ──
static void test_pbkdf2() {
    std::cout << "\n[PBKDF2-HMAC-SHA256] 測試向量\n";
    auto dk = pbkdf2_sha256("password", "salt", 1, 32);
    CHECK_EQ(to_hex(dk),
             "120fb6cffcf8b32c43e7225256c4f837a86548c92ccc35480805987cb70be17b",
             "iter=1, dkLen=32");

    auto dk2 = pbkdf2_sha256("password", "salt", 2, 32);
    CHECK_EQ(to_hex(dk2),
             "ae4d0c95af6b46d32d0adff928f06dd02a303f8ef3c251dfd6e2d85a95474c43",
             "iter=2, dkLen=32");
}

// ── Base64 / Base64URL ──
static void test_base64() {
    std::cout << "\n[Base64] RFC 4648\n";
    CHECK_EQ(base64_encode("f"), "Zg==", "\"f\"");
    CHECK_EQ(base64_encode("fo"), "Zm8=", "\"fo\"");
    CHECK_EQ(base64_encode("foo"), "Zm9v", "\"foo\"");
    CHECK_EQ(base64_encode("foobar"), "Zm9vYmFy", "\"foobar\"");

    std::string round = "MrLiouWord 怎麼過去，就怎麼回來";
    auto enc = base64_encode(round);
    auto dec = base64_decode(enc);
    CHECK_EQ(std::string(dec.begin(), dec.end()), round, "UTF-8 round-trip");

    // base64url 無 padding
    CHECK(b64url("f").find('=') == std::string::npos, "b64url has no padding");
}

// ── JSON 解析 / 序列化 ──
static void test_json() {
    std::cout << "\n[JSON] 解析與序列化\n";
    Json j = Json::parse(R"({"a":1,"b":"x","c":[1,2,3],"d":{"e":true},"f":null})");
    CHECK_EQ(j.at("a").as_int(), 1LL, "number field");
    CHECK_EQ(j.at("b").as_string(), "x", "string field");
    CHECK_EQ(j.at("c").size(), 3u, "array length");
    CHECK(j.at("d").at("e").as_bool(), "nested bool");
    CHECK(j.at("f").is_null(), "null field");
    CHECK(j.at("nonexistent").is_null(), "missing field → null");

    Json o = Json::object();
    o["msg"] = std::string("含跳脫\"字元\n換行");
    std::string dumped = o.dump();
    Json back = Json::parse(dumped);
    CHECK_EQ(back.at("msg").as_string(), "含跳脫\"字元\n換行", "escape round-trip");

    Json uni = Json::parse(R"({"k":"中文"})");
    CHECK_EQ(uni.at("k").as_string(), "中文", "\\uXXXX → UTF-8");
}

// ── Merkle 鏈 ──
static void test_merkle(const std::string& dir) {
    std::cout << "\n[Merkle] 追蹤鏈完整性\n";
    std::string tp = dir + "/t.jsonl";
    std::filesystem::remove(tp);
    std::filesystem::remove(tp + ".state.json");

    Tracer t(tp);
    std::string r0 = t.root();
    CHECK(r0.empty(), "genesis root is empty");

    Json p = Json::object();
    p["x"] = 1;
    std::string r1 = t.emit("ev.one", p);
    std::string r2 = t.emit("ev.two", p);
    std::string r3 = t.emit("ev.three", p);

    CHECK(r1 != r2 && r2 != r3, "each emit changes root");
    CHECK_EQ(t.tick(), 3u, "tick == 3");

    std::string err;
    CHECK(t.verify(&err), std::string("chain verifies: ") + (err.empty() ? "clean" : err));

    // 篡改偵測：改掉中間一行的 payload
    {
        std::ifstream in(tp);
        std::string all, line;
        int n = 0;
        while (std::getline(in, line)) {
            if (++n == 2) {
                size_t pos = line.find("\"x\":1");
                if (pos != std::string::npos) line.replace(pos, 5, "\"x\":9");
            }
            all += line + "\n";
        }
        in.close();
        std::ofstream out(tp, std::ios::trunc);
        out << all;
    }
    Tracer t2(tp);
    std::string err2;
    CHECK(!t2.verify(&err2), std::string("tamper detected: ") + err2);
}

// ── 密碼哈希 ──
static void test_password() {
    std::cout << "\n[Password] PBKDF2 哈希與驗證\n";
    // 用低迭代版本測邏輯（正式用 600000）
    std::string salt = "0011223344556677";
    auto dk = pbkdf2_sha256("correct horse", salt, 1000, 32);
    std::string stored = "pbkdf2_sha256$1000$" + salt + "$" + to_hex(dk);

    CHECK(verify_password("correct horse", stored), "correct password accepted");
    CHECK(!verify_password("wrong horse", stored), "wrong password rejected");
    CHECK(!verify_password("", stored), "empty password rejected");
    CHECK(!verify_password("correct horse", "garbage"), "malformed hash rejected");
    CHECK(!verify_password("correct horse", "pbkdf2_sha256$0$" + salt + "$x"),
          "zero iterations rejected");

    // 兩次哈希同一密碼 → 不同 salt → 不同結果
    std::string h1 = hash_password("same");
    std::string h2 = hash_password("same");
    CHECK(h1 != h2, "random salt makes hashes differ");
    CHECK(verify_password("same", h1) && verify_password("same", h2), "both verify");

    CHECK(secure_equals("abc", "abc"), "secure_equals match");
    CHECK(!secure_equals("abc", "abd"), "secure_equals mismatch");
    CHECK(!secure_equals("abc", "abcd"), "secure_equals length mismatch");
}

// ── JWT ──
static void test_jwt() {
    std::cout << "\n[JWT] HS256 簽發與驗證\n";
    std::string secret = "test_secret_do_not_use_in_prod";

    JwtClaims c;
    c.sub = "usr_123";
    c.iat = now_epoch_sec();
    c.exp = c.iat + 3600;
    c.jti = "jti_abc";
    std::string tok = jwt_sign(c, secret);

    CHECK(std::count(tok.begin(), tok.end(), '.') == 2, "token has 3 segments");

    auto v = jwt_verify(tok, secret);
    CHECK(v.valid, "valid token accepted");
    CHECK_EQ(v.payload.at("sub").as_string(), "usr_123", "sub claim");
    CHECK_EQ(v.payload.at("iss").as_string(), "mrliouai", "iss claim");
    CHECK_EQ(v.payload.at("origin_signature").as_string(), "MrLiouWord", "origin_signature claim");

    auto bad = jwt_verify(tok, "wrong_secret");
    CHECK(!bad.valid && bad.reason == "signature_mismatch", "wrong secret rejected");

    // 篡改 payload
    size_t d1 = tok.find('.'), d2 = tok.find('.', d1 + 1);
    std::string forged = tok.substr(0, d1 + 1) + b64url(R"({"sub":"admin","exp":9999999999})") +
                         tok.substr(d2);
    auto f = jwt_verify(forged, secret);
    CHECK(!f.valid, "forged payload rejected");

    // 過期
    JwtClaims old;
    old.sub = "usr_old";
    old.iat = now_epoch_sec() - 7200;
    old.exp = now_epoch_sec() - 3600;
    auto e = jwt_verify(jwt_sign(old, secret), secret);
    CHECK(!e.valid && e.reason == "expired", "expired token rejected");

    // alg=none 降級攻擊
    std::string none_tok = b64url(R"({"alg":"none","typ":"JWT"})") + "." +
                           b64url(R"({"sub":"admin"})") + ".";
    auto n = jwt_verify(none_tok, secret);
    CHECK(!n.valid, "alg=none rejected");

    CHECK(!jwt_verify("garbage", secret).valid, "malformed token rejected");
    CHECK(!jwt_verify("a.b", secret).valid, "two-segment token rejected");
}

// ── AuthService 端到端 ──
static void test_auth_service(const std::string& dir) {
    std::cout << "\n[AuthService] 端到端流程\n";
    std::string ad = dir + "/auth";
    std::filesystem::remove_all(ad);
    std::filesystem::create_directories(ad);

    AuthService auth(ad, "svc_secret_test");

    auto s1 = auth.signup("mr@liou.tw", "s3cure_password");
    CHECK(s1.ok && !s1.user_id.empty(), "signup ok");

    auto dup = auth.signup("mr@liou.tw", "another_password");
    CHECK(!dup.ok && dup.error == "email_already_registered", "duplicate email rejected");

    auto bad_email = auth.signup("notanemail", "s3cure_password");
    CHECK(!bad_email.ok && bad_email.error == "invalid_email", "invalid email rejected");

    auto short_pw = auth.signup("x@y.tw", "short");
    CHECK(!short_pw.ok && short_pw.error == "password_too_short_min_8", "short password rejected");

    auto in = auth.signin("mr@liou.tw", "s3cure_password");
    CHECK(in.ok && !in.access_token.empty() && !in.refresh_token.empty(), "signin issues tokens");
    CHECK_EQ(in.user_id, s1.user_id, "signin returns same user_id");

    auto wrong = auth.signin("mr@liou.tw", "wrong_password");
    CHECK(!wrong.ok && wrong.error == "invalid_credentials", "wrong password rejected");

    auto nouser = auth.signin("ghost@nowhere.tw", "whatever1");
    CHECK(!nouser.ok && nouser.error == "invalid_credentials", "unknown user → same error (no leak)");

    auto v = auth.verify(in.access_token);
    CHECK(v.valid && v.payload.at("sub").as_string() == s1.user_id, "access token verifies");

    auto rf = auth.refresh(in.refresh_token);
    CHECK(rf.ok && rf.refresh_token != in.refresh_token, "refresh rotates token");

    auto replay = auth.refresh(in.refresh_token);
    CHECK(!replay.ok && replay.error == "refresh_token_revoked", "old refresh token rejected (replay)");

    CHECK(auth.revoke(rf.refresh_token), "revoke ok");
    auto after_revoke = auth.refresh(rf.refresh_token);
    CHECK(!after_revoke.ok, "revoked token cannot refresh");

    CHECK_EQ(auth.user_count(), 1u, "user_count == 1");

    // 持久化：重載後帳號還在
    AuthService reloaded(ad, "svc_secret_test");
    CHECK_EQ(reloaded.user_count(), 1u, "persisted across reload");
    auto in2 = reloaded.signin("mr@liou.tw", "s3cure_password");
    CHECK(in2.ok, "signin works after reload");
}

// ── StoreService ──
static void test_store(const std::string& dir) {
    std::cout << "\n[StoreService] CRUD + 樂觀鎖 + 查詢\n";
    std::string sd = dir + "/store";
    std::filesystem::remove_all(sd);
    std::filesystem::create_directories(sd);

    StoreService store(sd);

    Json p = Json::object();
    p["title"] = std::string("粒子語言");
    p["status"] = std::string("active");

    auto c = store.create("notes", p, "n1");
    CHECK(c.ok && c.version == 1 && c.http_status == 201, "create returns v1/201");

    auto dup = store.create("notes", p, "n1");
    CHECK(!dup.ok && dup.http_status == 409, "duplicate create → 409");

    auto g = store.get("notes", "n1");
    CHECK(g.ok && g.doc.payload.at("title").as_string() == "粒子語言", "get returns payload");
    CHECK_EQ(g.doc.dl580_sync_state, "pending", "new doc pending DL580 sync");

    Json p2 = Json::object();
    p2["title"] = std::string("粒子語言 v2");
    p2["status"] = std::string("active");

    auto stale = store.update("notes", "n1", p2, 99);
    CHECK(!stale.ok && stale.http_status == 409 && stale.version == 1,
          "wrong expected_version → 409 with current version");

    auto u = store.update("notes", "n1", p2, 1);
    CHECK(u.ok && u.version == 2, "correct expected_version → v2");

    auto missing = store.update("notes", "nope", p2, 0);
    CHECK(!missing.ok && missing.http_status == 404, "update missing doc → 404");

    // 多筆 + 查詢
    for (int i = 0; i < 5; ++i) {
        Json q = Json::object();
        q["status"] = std::string(i % 2 == 0 ? "active" : "archived");
        q["idx"] = i;
        store.create("items", q, "i" + std::to_string(i));
    }
    auto all = store.query("items");
    CHECK_EQ(all.docs.size(), 5u, "query all in collection");

    auto act = store.query("items", "status", "active");
    CHECK_EQ(act.docs.size(), 3u, "field equality filter (3 active)");

    auto page1 = store.query("items", "", "", 2);
    CHECK(page1.docs.size() == 2 && !page1.complete && !page1.next_cursor.empty(),
          "pagination returns cursor");
    auto page2 = store.query("items", "", "", 2, page1.next_cursor);
    CHECK_EQ(page2.docs.size(), 2u, "cursor continues");
    CHECK(page1.docs[0].doc_id != page2.docs[0].doc_id, "pages do not overlap");

    // 軟刪除 — 資料保留
    auto d = store.soft_delete("items", "i0");
    CHECK(d.ok, "soft_delete ok");
    CHECK(!store.get("items", "i0").ok, "soft-deleted doc not returned by get");
    auto hist = store.history("items", "i0");
    CHECK(hist.size() >= 2, "version history retained after soft delete (法則: 不刪檔)");

    // 版本歷史
    auto h = store.history("notes", "n1");
    CHECK_EQ(h.size(), 2u, "notes/n1 has 2 versions");
    CHECK_EQ(h[0].at("op").as_string(), "create", "first version op=create");
    CHECK_EQ(h[1].at("op").as_string(), "update", "second version op=update");

    // DL580 sync
    auto pend = store.pending_sync();
    CHECK(!pend.empty(), "pending_sync lists unsynced docs");
    CHECK(store.mark_synced("notes", "n1"), "mark_synced ok");
    CHECK_EQ(store.get("notes", "n1").doc.dl580_sync_state, "synced", "sync state updated");

    // 持久化
    StoreService reloaded(sd);
    CHECK(reloaded.get("notes", "n1").ok, "persisted across reload");
    CHECK_EQ(reloaded.get("notes", "n1").doc.version, 2LL, "version persisted");
}

// ── Vault 沙箱 ──
static void test_vault(const std::string& dir) {
    std::cout << "\n[Vault] 沙箱與 traversal 防護\n";
    std::string vd = dir + "/vault";
    std::filesystem::remove_all(vd);

    Vault vault(vd);

    auto w = vault.write_text("hello.txt", "MrLiouWord");
    CHECK(w.at("ok").as_bool(), "write_text ok");
    CHECK_EQ(w.at("sha256").as_string(), SHA256::hex("MrLiouWord"), "sha256 correct");
    CHECK(!w.at("overwrote").as_bool(), "new file not marked overwrote");

    auto r = vault.read_text("hello.txt");
    CHECK(r.at("ok").as_bool() && r.at("content").as_string() == "MrLiouWord", "read_text ok");

    auto w2 = vault.write_text("hello.txt", "changed");
    CHECK(w2.at("overwrote").as_bool(), "overwrite flagged");
    CHECK_EQ(vault.read_text("hello.txt").at("content").as_string(), "changed", "content updated");

    CHECK(vault.mkdir("sub/deep").at("ok").as_bool(), "mkdir nested ok");
    CHECK(vault.write_text("sub/deep/f.txt", "x").at("ok").as_bool(), "write into nested dir");

    auto l = vault.list(".");
    CHECK(l.at("ok").as_bool() && l.at("count").as_int() >= 2, "list root");

    auto i = vault.info("hello.txt");
    CHECK(i.at("ok").as_bool() && i.at("type").as_string() == "file", "info file");
    CHECK_EQ(vault.info("sub").at("type").as_string(), "dir", "info dir");

    // traversal 攻擊全部要擋掉
    const char* attacks[] = {
        "../../../etc/passwd",
        "..",
        "sub/../../etc/passwd",
        "/etc/passwd",
        "./../../..",
    };
    for (const char* a : attacks) {
        auto res = vault.read_text(a);
        bool blocked = !res.at("ok").as_bool();
        CHECK(blocked, std::string("traversal blocked: ") + a);
    }

    auto wesc = vault.write_text("../escaped.txt", "should not land outside");
    CHECK(!wesc.at("ok").as_bool(), "write traversal blocked");

    CHECK(!vault.read_text("does_not_exist.txt").at("ok").as_bool(), "missing file → not ok");
    CHECK(!vault.read_text("sub").at("ok").as_bool(), "read_text on dir → not ok");
}

int main() {
    std::cout << "==========================================================\n"
              << " mrliouai_core selftest — origin_signature: MrLiouWord\n"
              << "==========================================================\n";

    std::string tmp = "./.selftest_tmp";
    std::filesystem::remove_all(tmp);
    std::filesystem::create_directories(tmp);

    test_sha256();
    test_hmac();
    test_pbkdf2();
    test_base64();
    test_json();
    test_merkle(tmp);
    test_password();
    test_jwt();
    test_auth_service(tmp);
    test_store(tmp);
    test_vault(tmp);

    std::filesystem::remove_all(tmp);

    std::cout << "\n==========================================================\n"
              << " PASS: " << g_pass << "   FAIL: " << g_fail << "\n"
              << "==========================================================\n";
    return g_fail == 0 ? 0 : 1;
}
