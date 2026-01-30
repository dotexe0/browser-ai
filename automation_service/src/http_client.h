#pragma once

#include "common.h"
#include <string>
#include <map>

/**
 * HTTP Client
 *
 * Simple WinHTTP wrapper for making GET/POST requests.
 * Used by AIProvider to call OpenAI, Anthropic, and Ollama APIs.
 */

struct HttpResponse {
    int statusCode;
    std::string body;
    std::string error;
    bool success;
};

class HttpClient {
public:
    HttpClient() = default;
    ~HttpClient() = default;

    // POST with JSON body and custom headers. Set useHttps=true for cloud APIs.
    HttpResponse Post(const std::wstring& host, int port, const std::wstring& path,
                      const std::string& body,
                      const std::map<std::string, std::string>& headers,
                      bool useHttps = false,
                      int timeoutMs = 60000);

    // GET with optional headers.
    HttpResponse Get(const std::wstring& host, int port, const std::wstring& path,
                     bool useHttps = false,
                     int timeoutMs = 5000);

private:
    // Read full response body from an open request handle
    std::string ReadResponseBody(void* hRequest);
};
