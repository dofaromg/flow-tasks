// mrliouai_core/include/mrl/base64.hpp
// Base64 / Base64URL 編解碼
// origin_signature: MrLiouWord
// 用途：JWT header/payload/signature 編碼（FireCore auth）
#pragma once

#include <cstdint>
#include <string>
#include <vector>

namespace mrl {

namespace detail {
inline const char* b64_std() {
    return "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
}
inline const char* b64_url() {
    return "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_";
}
}  // namespace detail

inline std::string base64_encode(const uint8_t* data, size_t len,
                                 bool url_safe = false, bool pad = true) {
    const char* tbl = url_safe ? detail::b64_url() : detail::b64_std();
    std::string out;
    out.reserve(((len + 2) / 3) * 4);

    size_t i = 0;
    while (i + 2 < len) {
        uint32_t n = (uint32_t(data[i]) << 16) | (uint32_t(data[i + 1]) << 8) | data[i + 2];
        out.push_back(tbl[(n >> 18) & 0x3f]);
        out.push_back(tbl[(n >> 12) & 0x3f]);
        out.push_back(tbl[(n >> 6) & 0x3f]);
        out.push_back(tbl[n & 0x3f]);
        i += 3;
    }

    if (i + 1 == len) {
        uint32_t n = uint32_t(data[i]) << 16;
        out.push_back(tbl[(n >> 18) & 0x3f]);
        out.push_back(tbl[(n >> 12) & 0x3f]);
        if (pad) { out.push_back('='); out.push_back('='); }
    } else if (i + 2 == len) {
        uint32_t n = (uint32_t(data[i]) << 16) | (uint32_t(data[i + 1]) << 8);
        out.push_back(tbl[(n >> 18) & 0x3f]);
        out.push_back(tbl[(n >> 12) & 0x3f]);
        out.push_back(tbl[(n >> 6) & 0x3f]);
        if (pad) out.push_back('=');
    }
    return out;
}

inline std::string base64_encode(const std::string& s, bool url_safe = false, bool pad = true) {
    return base64_encode(reinterpret_cast<const uint8_t*>(s.data()), s.size(), url_safe, pad);
}

inline std::vector<uint8_t> base64_decode(const std::string& in, bool url_safe = false) {
    const char* tbl = url_safe ? detail::b64_url() : detail::b64_std();
    int rev[256];
    for (int i = 0; i < 256; ++i) rev[i] = -1;
    for (int i = 0; i < 64; ++i) rev[static_cast<unsigned char>(tbl[i])] = i;

    std::vector<uint8_t> out;
    out.reserve(in.size() * 3 / 4);
    uint32_t buf = 0;
    int bits = 0;

    for (char c : in) {
        if (c == '=' || c == '\n' || c == '\r') continue;
        int v = rev[static_cast<unsigned char>(c)];
        if (v < 0) continue;
        buf = (buf << 6) | static_cast<uint32_t>(v);
        bits += 6;
        if (bits >= 8) {
            bits -= 8;
            out.push_back(static_cast<uint8_t>((buf >> bits) & 0xff));
        }
    }
    return out;
}

// JWT 用：base64url 無 padding
inline std::string b64url(const std::string& s) { return base64_encode(s, true, false); }

inline std::string b64url(const uint8_t* d, size_t n) {
    return base64_encode(d, n, true, false);
}

inline std::string b64url_decode_str(const std::string& s) {
    auto v = base64_decode(s, true);
    return std::string(v.begin(), v.end());
}

}  // namespace mrl
