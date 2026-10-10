// mrliouai_core/include/mrl/sha256.hpp
// SHA-256 + HMAC-SHA256 + PBKDF2-HMAC-SHA256
// origin_signature: MrLiouWord
// 自持實作，零外部依賴（不用 OpenSSL）
// 對應規格：flowcontainer.py / flowcore_loop.py 的 Merkle 鏈 SHA-256
#pragma once

#include <array>
#include <cstdint>
#include <cstring>
#include <string>
#include <vector>

namespace mrl {

class SHA256 {
public:
    static constexpr size_t DIGEST_SIZE = 32;
    static constexpr size_t BLOCK_SIZE = 64;

    SHA256() { reset(); }

    void reset() {
        h_[0] = 0x6a09e667u; h_[1] = 0xbb67ae85u;
        h_[2] = 0x3c6ef372u; h_[3] = 0xa54ff53au;
        h_[4] = 0x510e527fu; h_[5] = 0x9b05688cu;
        h_[6] = 0x1f83d9abu; h_[7] = 0x5be0cd19u;
        buf_len_ = 0;
        total_ = 0;
    }

    void update(const uint8_t* data, size_t len) {
        total_ += len;
        while (len > 0) {
            size_t take = BLOCK_SIZE - buf_len_;
            if (take > len) take = len;
            std::memcpy(buf_ + buf_len_, data, take);
            buf_len_ += take;
            data += take;
            len -= take;
            if (buf_len_ == BLOCK_SIZE) {
                transform(buf_);
                buf_len_ = 0;
            }
        }
    }

    void update(const std::string& s) {
        update(reinterpret_cast<const uint8_t*>(s.data()), s.size());
    }

    std::array<uint8_t, DIGEST_SIZE> digest() {
        uint64_t bit_len = total_ * 8;
        uint8_t pad = 0x80;
        update(&pad, 1);
        uint8_t zero = 0x00;
        while (buf_len_ != 56) update(&zero, 1);
        uint8_t len_be[8];
        for (int i = 0; i < 8; ++i)
            len_be[i] = static_cast<uint8_t>((bit_len >> (56 - 8 * i)) & 0xff);
        total_ -= 8;  // length bytes are not message content
        update(len_be, 8);

        std::array<uint8_t, DIGEST_SIZE> out{};
        for (int i = 0; i < 8; ++i) {
            out[i * 4 + 0] = static_cast<uint8_t>((h_[i] >> 24) & 0xff);
            out[i * 4 + 1] = static_cast<uint8_t>((h_[i] >> 16) & 0xff);
            out[i * 4 + 2] = static_cast<uint8_t>((h_[i] >> 8) & 0xff);
            out[i * 4 + 3] = static_cast<uint8_t>(h_[i] & 0xff);
        }
        return out;
    }

    static std::string hex(const std::string& msg) {
        SHA256 s;
        s.update(msg);
        return to_hex(s.digest());
    }

    static std::array<uint8_t, DIGEST_SIZE> raw(const uint8_t* data, size_t len) {
        SHA256 s;
        s.update(data, len);
        return s.digest();
    }

    static std::string to_hex(const std::array<uint8_t, DIGEST_SIZE>& d) {
        static const char* k = "0123456789abcdef";
        std::string out;
        out.reserve(DIGEST_SIZE * 2);
        for (uint8_t b : d) {
            out.push_back(k[b >> 4]);
            out.push_back(k[b & 0x0f]);
        }
        return out;
    }

private:
    static uint32_t rotr(uint32_t x, int n) { return (x >> n) | (x << (32 - n)); }

    void transform(const uint8_t* p) {
        static const uint32_t K[64] = {
            0x428a2f98u,0x71374491u,0xb5c0fbcfu,0xe9b5dba5u,0x3956c25bu,0x59f111f1u,
            0x923f82a4u,0xab1c5ed5u,0xd807aa98u,0x12835b01u,0x243185beu,0x550c7dc3u,
            0x72be5d74u,0x80deb1feu,0x9bdc06a7u,0xc19bf174u,0xe49b69c1u,0xefbe4786u,
            0x0fc19dc6u,0x240ca1ccu,0x2de92c6fu,0x4a7484aau,0x5cb0a9dcu,0x76f988dau,
            0x983e5152u,0xa831c66du,0xb00327c8u,0xbf597fc7u,0xc6e00bf3u,0xd5a79147u,
            0x06ca6351u,0x14292967u,0x27b70a85u,0x2e1b2138u,0x4d2c6dfcu,0x53380d13u,
            0x650a7354u,0x766a0abbu,0x81c2c92eu,0x92722c85u,0xa2bfe8a1u,0xa81a664bu,
            0xc24b8b70u,0xc76c51a3u,0xd192e819u,0xd6990624u,0xf40e3585u,0x106aa070u,
            0x19a4c116u,0x1e376c08u,0x2748774cu,0x34b0bcb5u,0x391c0cb3u,0x4ed8aa4au,
            0x5b9cca4fu,0x682e6ff3u,0x748f82eeu,0x78a5636fu,0x84c87814u,0x8cc70208u,
            0x90befffau,0xa4506cebu,0xbef9a3f7u,0xc67178f2u};

        uint32_t w[64];
        for (int i = 0; i < 16; ++i)
            w[i] = (uint32_t(p[i * 4]) << 24) | (uint32_t(p[i * 4 + 1]) << 16) |
                   (uint32_t(p[i * 4 + 2]) << 8) | uint32_t(p[i * 4 + 3]);
        for (int i = 16; i < 64; ++i) {
            uint32_t s0 = rotr(w[i - 15], 7) ^ rotr(w[i - 15], 18) ^ (w[i - 15] >> 3);
            uint32_t s1 = rotr(w[i - 2], 17) ^ rotr(w[i - 2], 19) ^ (w[i - 2] >> 10);
            w[i] = w[i - 16] + s0 + w[i - 7] + s1;
        }

        uint32_t a = h_[0], b = h_[1], c = h_[2], d = h_[3];
        uint32_t e = h_[4], f = h_[5], g = h_[6], hh = h_[7];

        for (int i = 0; i < 64; ++i) {
            uint32_t S1 = rotr(e, 6) ^ rotr(e, 11) ^ rotr(e, 25);
            uint32_t ch = (e & f) ^ ((~e) & g);
            uint32_t t1 = hh + S1 + ch + K[i] + w[i];
            uint32_t S0 = rotr(a, 2) ^ rotr(a, 13) ^ rotr(a, 22);
            uint32_t maj = (a & b) ^ (a & c) ^ (b & c);
            uint32_t t2 = S0 + maj;
            hh = g; g = f; f = e; e = d + t1;
            d = c; c = b; b = a; a = t1 + t2;
        }

        h_[0] += a; h_[1] += b; h_[2] += c; h_[3] += d;
        h_[4] += e; h_[5] += f; h_[6] += g; h_[7] += hh;
    }

    uint32_t h_[8]{};
    uint8_t buf_[BLOCK_SIZE]{};
    size_t buf_len_ = 0;
    uint64_t total_ = 0;
};

// ── HMAC-SHA256 ──
inline std::array<uint8_t, 32> hmac_sha256(const uint8_t* key, size_t key_len,
                                          const uint8_t* msg, size_t msg_len) {
    uint8_t k[SHA256::BLOCK_SIZE] = {0};
    if (key_len > SHA256::BLOCK_SIZE) {
        auto kd = SHA256::raw(key, key_len);
        std::memcpy(k, kd.data(), kd.size());
    } else {
        std::memcpy(k, key, key_len);
    }

    uint8_t ipad[SHA256::BLOCK_SIZE], opad[SHA256::BLOCK_SIZE];
    for (size_t i = 0; i < SHA256::BLOCK_SIZE; ++i) {
        ipad[i] = k[i] ^ 0x36;
        opad[i] = k[i] ^ 0x5c;
    }

    SHA256 inner;
    inner.update(ipad, SHA256::BLOCK_SIZE);
    inner.update(msg, msg_len);
    auto inner_d = inner.digest();

    SHA256 outer;
    outer.update(opad, SHA256::BLOCK_SIZE);
    outer.update(inner_d.data(), inner_d.size());
    return outer.digest();
}

inline std::array<uint8_t, 32> hmac_sha256(const std::string& key, const std::string& msg) {
    return hmac_sha256(reinterpret_cast<const uint8_t*>(key.data()), key.size(),
                       reinterpret_cast<const uint8_t*>(msg.data()), msg.size());
}

// ── PBKDF2-HMAC-SHA256 ──
// 密碼哈希：取代 FireCore auth 模組的 202 stub
inline std::vector<uint8_t> pbkdf2_sha256(const std::string& password,
                                          const std::string& salt,
                                          uint32_t iterations,
                                          size_t dk_len) {
    std::vector<uint8_t> out;
    out.reserve(dk_len);
    uint32_t block = 1;

    while (out.size() < dk_len) {
        std::string msg = salt;
        msg.push_back(static_cast<char>((block >> 24) & 0xff));
        msg.push_back(static_cast<char>((block >> 16) & 0xff));
        msg.push_back(static_cast<char>((block >> 8) & 0xff));
        msg.push_back(static_cast<char>(block & 0xff));

        auto u = hmac_sha256(reinterpret_cast<const uint8_t*>(password.data()), password.size(),
                             reinterpret_cast<const uint8_t*>(msg.data()), msg.size());
        auto t = u;

        for (uint32_t i = 1; i < iterations; ++i) {
            u = hmac_sha256(reinterpret_cast<const uint8_t*>(password.data()), password.size(),
                            u.data(), u.size());
            for (size_t j = 0; j < t.size(); ++j) t[j] ^= u[j];
        }

        for (size_t j = 0; j < t.size() && out.size() < dk_len; ++j)
            out.push_back(t[j]);
        ++block;
    }
    return out;
}

inline std::string to_hex(const std::vector<uint8_t>& v) {
    static const char* k = "0123456789abcdef";
    std::string out;
    out.reserve(v.size() * 2);
    for (uint8_t b : v) {
        out.push_back(k[b >> 4]);
        out.push_back(k[b & 0x0f]);
    }
    return out;
}

// 常數時間比較 — 防 timing attack
inline bool secure_equals(const std::string& a, const std::string& b) {
    if (a.size() != b.size()) return false;
    unsigned char diff = 0;
    for (size_t i = 0; i < a.size(); ++i)
        diff |= static_cast<unsigned char>(a[i]) ^ static_cast<unsigned char>(b[i]);
    return diff == 0;
}

}  // namespace mrl
