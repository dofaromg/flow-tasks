// mrliouai_core/include/mrl/json.hpp
// 最小 JSON 值 / 解析 / 序列化
// origin_signature: MrLiouWord
// 零外部依賴，支援 object/array/string/number/bool/null
#pragma once

#include <cctype>
#include <cstdlib>
#include <iomanip>
#include <map>
#include <memory>
#include <sstream>
#include <string>
#include <vector>

namespace mrl {

class Json {
public:
    enum class Type { Null, Bool, Number, String, Array, Object };

    Json() : type_(Type::Null) {}
    Json(bool b) : type_(Type::Bool), bool_(b) {}
    Json(double d) : type_(Type::Number), num_(d) {}
    Json(int i) : type_(Type::Number), num_(static_cast<double>(i)) {}
    Json(long long i) : type_(Type::Number), num_(static_cast<double>(i)) {}
    Json(const char* s) : type_(Type::String), str_(s) {}
    Json(std::string s) : type_(Type::String), str_(std::move(s)) {}

    static Json object() { Json j; j.type_ = Type::Object; return j; }
    static Json array() { Json j; j.type_ = Type::Array; return j; }

    Type type() const { return type_; }
    bool is_null() const { return type_ == Type::Null; }
    bool is_object() const { return type_ == Type::Object; }
    bool is_array() const { return type_ == Type::Array; }
    bool is_string() const { return type_ == Type::String; }
    bool is_number() const { return type_ == Type::Number; }
    bool is_bool() const { return type_ == Type::Bool; }

    // object 存取
    Json& operator[](const std::string& k) {
        if (type_ != Type::Object) { type_ = Type::Object; obj_.clear(); }
        return obj_[k];
    }

    const Json& at(const std::string& k) const {
        static const Json null_json;
        auto it = obj_.find(k);
        return it == obj_.end() ? null_json : it->second;
    }

    bool has(const std::string& k) const { return obj_.find(k) != obj_.end(); }

    // array 存取
    void push(Json v) {
        if (type_ != Type::Array) { type_ = Type::Array; arr_.clear(); }
        arr_.push_back(std::move(v));
    }

    size_t size() const {
        if (type_ == Type::Array) return arr_.size();
        if (type_ == Type::Object) return obj_.size();
        if (type_ == Type::String) return str_.size();
        return 0;
    }

    const std::vector<Json>& items() const { return arr_; }
    const std::map<std::string, Json>& fields() const { return obj_; }

    // 取值（帶預設）
    std::string as_string(const std::string& def = "") const {
        return type_ == Type::String ? str_ : def;
    }
    double as_number(double def = 0) const { return type_ == Type::Number ? num_ : def; }
    long long as_int(long long def = 0) const {
        return type_ == Type::Number ? static_cast<long long>(num_) : def;
    }
    bool as_bool(bool def = false) const { return type_ == Type::Bool ? bool_ : def; }

    // ── 序列化 ──
    std::string dump(int indent = -1, int depth = 0) const {
        std::ostringstream o;
        write(o, indent, depth);
        return o.str();
    }

    // ── 解析 ──
    static Json parse(const std::string& s) {
        size_t i = 0;
        Json j = parse_value(s, i);
        return j;
    }

private:
    void write(std::ostringstream& o, int indent, int depth) const {
        const bool pretty = indent >= 0;
        const std::string nl = pretty ? "\n" : "";
        const std::string pad = pretty ? std::string(static_cast<size_t>(indent * (depth + 1)), ' ') : "";
        const std::string pad_end = pretty ? std::string(static_cast<size_t>(indent * depth), ' ') : "";

        switch (type_) {
            case Type::Null: o << "null"; break;
            case Type::Bool: o << (bool_ ? "true" : "false"); break;
            case Type::Number: {
                if (num_ == static_cast<double>(static_cast<long long>(num_))) {
                    o << static_cast<long long>(num_);
                } else {
                    // 17 位有效數字 = double 的無損來回精度
                    // （PHI = 1.618033988749895 必須原樣保存）
                    std::ostringstream t;
                    t << std::setprecision(17) << num_;
                    std::string s = t.str();
                    // 修掉尾隨零：1.6180339887498949 → 保留，但 2.5000000000000000 → 2.5
                    if (s.find('e') == std::string::npos && s.find('.') != std::string::npos) {
                        size_t last = s.find_last_not_of('0');
                        if (last != std::string::npos && s[last] == '.') ++last;
                        s.erase(last + 1);
                    }
                    o << s;
                }
                break;
            }
            case Type::String: escape(o, str_); break;
            case Type::Array: {
                if (arr_.empty()) { o << "[]"; break; }
                o << "[" << nl;
                for (size_t k = 0; k < arr_.size(); ++k) {
                    o << pad;
                    arr_[k].write(o, indent, depth + 1);
                    if (k + 1 < arr_.size()) o << ",";
                    o << nl;
                }
                o << pad_end << "]";
                break;
            }
            case Type::Object: {
                if (obj_.empty()) { o << "{}"; break; }
                o << "{" << nl;
                size_t k = 0;
                for (const auto& kv : obj_) {
                    o << pad;
                    escape(o, kv.first);
                    o << (pretty ? ": " : ":");
                    kv.second.write(o, indent, depth + 1);
                    if (++k < obj_.size()) o << ",";
                    o << nl;
                }
                o << pad_end << "}";
                break;
            }
        }
    }

    static void escape(std::ostringstream& o, const std::string& s) {
        o << '"';
        for (unsigned char c : s) {
            switch (c) {
                case '"': o << "\\\""; break;
                case '\\': o << "\\\\"; break;
                case '\n': o << "\\n"; break;
                case '\r': o << "\\r"; break;
                case '\t': o << "\\t"; break;
                case '\b': o << "\\b"; break;
                case '\f': o << "\\f"; break;
                default:
                    if (c < 0x20) {
                        static const char* hx = "0123456789abcdef";
                        o << "\\u00" << hx[c >> 4] << hx[c & 0x0f];
                    } else {
                        o << static_cast<char>(c);
                    }
            }
        }
        o << '"';
    }

    static void skip_ws(const std::string& s, size_t& i) {
        while (i < s.size() && (s[i] == ' ' || s[i] == '\t' || s[i] == '\n' || s[i] == '\r')) ++i;
    }

    static Json parse_value(const std::string& s, size_t& i) {
        skip_ws(s, i);
        if (i >= s.size()) return Json();

        char c = s[i];
        if (c == '{') return parse_object(s, i);
        if (c == '[') return parse_array(s, i);
        if (c == '"') return Json(parse_string(s, i));
        if (c == 't') { i += 4; return Json(true); }
        if (c == 'f') { i += 5; return Json(false); }
        if (c == 'n') { i += 4; return Json(); }
        return parse_number(s, i);
    }

    static Json parse_object(const std::string& s, size_t& i) {
        Json j = Json::object();
        ++i;  // '{'
        skip_ws(s, i);
        if (i < s.size() && s[i] == '}') { ++i; return j; }
        while (i < s.size()) {
            skip_ws(s, i);
            if (i >= s.size() || s[i] != '"') break;
            std::string key = parse_string(s, i);
            skip_ws(s, i);
            if (i < s.size() && s[i] == ':') ++i;
            j.obj_[key] = parse_value(s, i);
            skip_ws(s, i);
            if (i < s.size() && s[i] == ',') { ++i; continue; }
            if (i < s.size() && s[i] == '}') { ++i; break; }
            break;
        }
        return j;
    }

    static Json parse_array(const std::string& s, size_t& i) {
        Json j = Json::array();
        ++i;  // '['
        skip_ws(s, i);
        if (i < s.size() && s[i] == ']') { ++i; return j; }
        while (i < s.size()) {
            j.arr_.push_back(parse_value(s, i));
            skip_ws(s, i);
            if (i < s.size() && s[i] == ',') { ++i; continue; }
            if (i < s.size() && s[i] == ']') { ++i; break; }
            break;
        }
        return j;
    }

    static std::string parse_string(const std::string& s, size_t& i) {
        std::string out;
        ++i;  // opening quote
        while (i < s.size() && s[i] != '"') {
            if (s[i] == '\\' && i + 1 < s.size()) {
                ++i;
                switch (s[i]) {
                    case 'n': out.push_back('\n'); break;
                    case 't': out.push_back('\t'); break;
                    case 'r': out.push_back('\r'); break;
                    case 'b': out.push_back('\b'); break;
                    case 'f': out.push_back('\f'); break;
                    case 'u': {
                        if (i + 4 < s.size()) {
                            std::string hex = s.substr(i + 1, 4);
                            unsigned cp = static_cast<unsigned>(std::strtoul(hex.c_str(), nullptr, 16));
                            // UTF-8 編碼
                            if (cp < 0x80) {
                                out.push_back(static_cast<char>(cp));
                            } else if (cp < 0x800) {
                                out.push_back(static_cast<char>(0xC0 | (cp >> 6)));
                                out.push_back(static_cast<char>(0x80 | (cp & 0x3F)));
                            } else {
                                out.push_back(static_cast<char>(0xE0 | (cp >> 12)));
                                out.push_back(static_cast<char>(0x80 | ((cp >> 6) & 0x3F)));
                                out.push_back(static_cast<char>(0x80 | (cp & 0x3F)));
                            }
                            i += 4;
                        }
                        break;
                    }
                    default: out.push_back(s[i]);
                }
            } else {
                out.push_back(s[i]);
            }
            ++i;
        }
        if (i < s.size()) ++i;  // closing quote
        return out;
    }

    static Json parse_number(const std::string& s, size_t& i) {
        size_t start = i;
        if (i < s.size() && (s[i] == '-' || s[i] == '+')) ++i;
        while (i < s.size() && (std::isdigit(static_cast<unsigned char>(s[i])) ||
                                s[i] == '.' || s[i] == 'e' || s[i] == 'E' ||
                                s[i] == '-' || s[i] == '+'))
            ++i;
        return Json(std::strtod(s.substr(start, i - start).c_str(), nullptr));
    }

    Type type_;
    bool bool_ = false;
    double num_ = 0;
    std::string str_;
    std::vector<Json> arr_;
    std::map<std::string, Json> obj_;
};

}  // namespace mrl
