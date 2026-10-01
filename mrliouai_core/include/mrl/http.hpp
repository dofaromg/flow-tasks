// mrliouai_core/include/mrl/http.hpp
// POSIX socket HTTP/1.1 伺服器 + 路由
// origin_signature: MrLiouWord
// 對應規格：flowcore_loop.py 的 ThreadingHTTPServer
// 零外部依賴，thread-per-connection
#pragma once

#include <arpa/inet.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <sys/socket.h>
#include <unistd.h>

#include <algorithm>
#include <atomic>
#include <cstring>
#include <functional>
#include <map>
#include <sstream>
#include <string>
#include <thread>
#include <vector>

#include "json.hpp"

namespace mrl {

struct Request {
    std::string method;
    std::string path;
    std::string raw_query;
    std::map<std::string, std::string> query;
    std::map<std::string, std::string> headers;  // 鍵一律小寫
    std::string body;

    std::string header(const std::string& k, const std::string& def = "") const {
        std::string lk = k;
        std::transform(lk.begin(), lk.end(), lk.begin(), ::tolower);
        auto it = headers.find(lk);
        return it == headers.end() ? def : it->second;
    }

    std::string q(const std::string& k, const std::string& def = "") const {
        auto it = query.find(k);
        return it == query.end() ? def : it->second;
    }

    Json json() const { return body.empty() ? Json::object() : Json::parse(body); }
};

struct Response {
    int status = 200;
    std::string content_type = "application/json; charset=utf-8";
    std::string body;
    std::map<std::string, std::string> extra_headers;

    static Response json(const Json& j, int status = 200) {
        Response r;
        r.status = status;
        r.body = j.dump(2);
        return r;
    }

    static Response text(const std::string& s, int status = 200) {
        Response r;
        r.status = status;
        r.content_type = "text/plain; charset=utf-8";
        r.body = s;
        return r;
    }
};

inline const char* status_text(int code) {
    switch (code) {
        case 200: return "OK";
        case 201: return "Created";
        case 202: return "Accepted";
        case 204: return "No Content";
        case 400: return "Bad Request";
        case 401: return "Unauthorized";
        case 403: return "Forbidden";
        case 404: return "Not Found";
        case 405: return "Method Not Allowed";
        case 409: return "Conflict";
        case 413: return "Payload Too Large";
        case 422: return "Unprocessable Entity";
        case 429: return "Too Many Requests";
        case 500: return "Internal Server Error";
        case 503: return "Service Unavailable";
        default: return "Unknown";
    }
}

inline std::string url_decode(const std::string& s) {
    std::string out;
    out.reserve(s.size());
    for (size_t i = 0; i < s.size(); ++i) {
        if (s[i] == '%' && i + 2 < s.size()) {
            int hi = std::isxdigit(static_cast<unsigned char>(s[i + 1]))
                         ? (std::isdigit(static_cast<unsigned char>(s[i + 1]))
                                ? s[i + 1] - '0'
                                : std::tolower(s[i + 1]) - 'a' + 10)
                         : -1;
            int lo = std::isxdigit(static_cast<unsigned char>(s[i + 2]))
                         ? (std::isdigit(static_cast<unsigned char>(s[i + 2]))
                                ? s[i + 2] - '0'
                                : std::tolower(s[i + 2]) - 'a' + 10)
                         : -1;
            if (hi >= 0 && lo >= 0) {
                out.push_back(static_cast<char>(hi * 16 + lo));
                i += 2;
                continue;
            }
        }
        if (s[i] == '+') { out.push_back(' '); continue; }
        out.push_back(s[i]);
    }
    return out;
}

class Server {
public:
    using Handler = std::function<Response(const Request&)>;

    // 路由：method + path prefix。前綴比對，長的優先。
    void route(const std::string& method, const std::string& prefix, Handler h) {
        routes_.push_back({method, prefix, std::move(h)});
        std::sort(routes_.begin(), routes_.end(),
                  [](const Route& a, const Route& b) {
                      return a.prefix.size() > b.prefix.size();
                  });
    }

    void get(const std::string& p, Handler h) { route("GET", p, std::move(h)); }
    void post(const std::string& p, Handler h) { route("POST", p, std::move(h)); }
    void put(const std::string& p, Handler h) { route("PUT", p, std::move(h)); }
    void del(const std::string& p, Handler h) { route("DELETE", p, std::move(h)); }

    // 全域中間件：回傳非空 Response 即短路
    void before(std::function<bool(const Request&, Response&)> mw) {
        middleware_.push_back(std::move(mw));
    }

    bool listen(const std::string& host, uint16_t port) {
        fd_ = ::socket(AF_INET, SOCK_STREAM, 0);
        if (fd_ < 0) return false;

        int on = 1;
        ::setsockopt(fd_, SOL_SOCKET, SO_REUSEADDR, &on, sizeof(on));

        sockaddr_in addr{};
        addr.sin_family = AF_INET;
        addr.sin_port = htons(port);
        if (::inet_pton(AF_INET, host.c_str(), &addr.sin_addr) != 1) {
            addr.sin_addr.s_addr = htonl(INADDR_ANY);
        }

        if (::bind(fd_, reinterpret_cast<sockaddr*>(&addr), sizeof(addr)) < 0) {
            ::close(fd_);
            fd_ = -1;
            return false;
        }
        if (::listen(fd_, 128) < 0) {
            ::close(fd_);
            fd_ = -1;
            return false;
        }
        running_ = true;
        return true;
    }

    void serve_forever() {
        while (running_) {
            sockaddr_in cli{};
            socklen_t len = sizeof(cli);
            int cfd = ::accept(fd_, reinterpret_cast<sockaddr*>(&cli), &len);
            if (cfd < 0) {
                if (!running_) break;
                continue;
            }
            std::thread(&Server::handle_conn, this, cfd).detach();
        }
    }

    void stop() {
        running_ = false;
        if (fd_ >= 0) { ::close(fd_); fd_ = -1; }
    }

    ~Server() { stop(); }

private:
    struct Route {
        std::string method;
        std::string prefix;
        Handler handler;
    };

    void handle_conn(int cfd) {
        int on = 1;
        ::setsockopt(cfd, IPPROTO_TCP, TCP_NODELAY, &on, sizeof(on));

        std::string raw;
        char buf[8192];
        size_t header_end = std::string::npos;

        // 讀 header
        while (true) {
            ssize_t n = ::recv(cfd, buf, sizeof(buf), 0);
            if (n <= 0) { ::close(cfd); return; }
            raw.append(buf, static_cast<size_t>(n));
            header_end = raw.find("\r\n\r\n");
            if (header_end != std::string::npos) break;
            if (raw.size() > 64 * 1024) { ::close(cfd); return; }
        }

        Request req;
        if (!parse_head(raw.substr(0, header_end), req)) {
            send_response(cfd, Response::json(err_json("bad_request"), 400));
            ::close(cfd);
            return;
        }

        // 讀 body
        size_t content_len = 0;
        auto cl = req.headers.find("content-length");
        if (cl != req.headers.end()) content_len = std::strtoul(cl->second.c_str(), nullptr, 10);

        if (content_len > MAX_BODY) {
            send_response(cfd, Response::json(err_json("payload_too_large"), 413));
            ::close(cfd);
            return;
        }

        req.body = raw.substr(header_end + 4);
        while (req.body.size() < content_len) {
            ssize_t n = ::recv(cfd, buf, sizeof(buf), 0);
            if (n <= 0) break;
            req.body.append(buf, static_cast<size_t>(n));
        }
        if (req.body.size() > content_len) req.body.resize(content_len);

        // CORS preflight
        if (req.method == "OPTIONS") {
            Response r;
            r.status = 204;
            r.extra_headers["access-control-allow-methods"] = "GET,POST,PUT,PATCH,DELETE,OPTIONS";
            r.extra_headers["access-control-allow-headers"] =
                "content-type, authorization, x-mrl-origin-signature, x-human-token, x-master-key";
            send_response(cfd, r);
            ::close(cfd);
            return;
        }

        Response res = dispatch(req);
        send_response(cfd, res);
        ::close(cfd);
    }

    Response dispatch(const Request& req) {
        for (auto& mw : middleware_) {
            Response early;
            if (!mw(req, early)) return early;
        }
        for (const auto& r : routes_) {
            if (r.method != req.method) continue;
            if (req.path.rfind(r.prefix, 0) != 0) continue;
            try {
                return r.handler(req);
            } catch (const std::exception& e) {
                Json j = Json::object();
                j["ok"] = false;
                j["error"] = std::string("handler_exception");
                j["detail"] = std::string(e.what());
                j["origin_signature"] = std::string("MrLiouWord");
                return Response::json(j, 500);
            }
        }
        Json j = err_json("route_not_registered");
        j["path"] = req.path;
        j["method"] = req.method;
        return Response::json(j, 404);
    }

    static Json err_json(const std::string& code) {
        Json j = Json::object();
        j["ok"] = false;
        j["error"] = code;
        j["origin_signature"] = std::string("MrLiouWord");
        return j;
    }

    static bool parse_head(const std::string& head, Request& req) {
        std::istringstream is(head);
        std::string line;
        if (!std::getline(is, line)) return false;
        if (!line.empty() && line.back() == '\r') line.pop_back();

        std::istringstream ls(line);
        std::string target, version;
        if (!(ls >> req.method >> target >> version)) return false;

        size_t qpos = target.find('?');
        if (qpos == std::string::npos) {
            req.path = url_decode(target);
        } else {
            req.path = url_decode(target.substr(0, qpos));
            req.raw_query = target.substr(qpos + 1);
            std::istringstream qs(req.raw_query);
            std::string pair;
            while (std::getline(qs, pair, '&')) {
                size_t eq = pair.find('=');
                if (eq == std::string::npos)
                    req.query[url_decode(pair)] = "";
                else
                    req.query[url_decode(pair.substr(0, eq))] = url_decode(pair.substr(eq + 1));
            }
        }

        while (std::getline(is, line)) {
            if (!line.empty() && line.back() == '\r') line.pop_back();
            if (line.empty()) break;
            size_t c = line.find(':');
            if (c == std::string::npos) continue;
            std::string k = line.substr(0, c);
            std::string v = line.substr(c + 1);
            while (!v.empty() && (v.front() == ' ' || v.front() == '\t')) v.erase(v.begin());
            std::transform(k.begin(), k.end(), k.begin(), ::tolower);
            req.headers[k] = v;
        }
        return true;
    }

    static void send_response(int cfd, const Response& res) {
        std::ostringstream o;
        o << "HTTP/1.1 " << res.status << " " << status_text(res.status) << "\r\n"
          << "content-type: " << res.content_type << "\r\n"
          << "content-length: " << res.body.size() << "\r\n"
          << "x-mrl-origin-signature: MrLiouWord\r\n"
          << "access-control-allow-origin: *\r\n"
          << "access-control-expose-headers: x-mrl-origin-signature\r\n"
          << "cache-control: no-store\r\n"
          << "connection: close\r\n";
        for (const auto& kv : res.extra_headers)
            o << kv.first << ": " << kv.second << "\r\n";
        o << "\r\n" << res.body;

        std::string out = o.str();
        size_t sent = 0;
        while (sent < out.size()) {
            ssize_t n = ::send(cfd, out.data() + sent, out.size() - sent, MSG_NOSIGNAL);
            if (n <= 0) break;
            sent += static_cast<size_t>(n);
        }
    }

    static constexpr size_t MAX_BODY = 8 * 1024 * 1024;

    int fd_ = -1;
    std::atomic<bool> running_{false};
    std::vector<Route> routes_;
    std::vector<std::function<bool(const Request&, Response&)>> middleware_;
};

}  // namespace mrl
