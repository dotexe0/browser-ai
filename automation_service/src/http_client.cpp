#include "http_client.h"
#include <winhttp.h>
#include <vector>
#include <sstream>

#pragma comment(lib, "Winhttp.lib")

std::string HttpClient::ReadResponseBody(void* hRequest) {
    std::string body;
    DWORD bytesAvailable = 0;
    while (WinHttpQueryDataAvailable(static_cast<HINTERNET>(hRequest), &bytesAvailable)
           && bytesAvailable > 0) {
        std::vector<char> buf(bytesAvailable);
        DWORD bytesRead = 0;
        WinHttpReadData(static_cast<HINTERNET>(hRequest),
                        buf.data(), bytesAvailable, &bytesRead);
        body.append(buf.data(), bytesRead);
    }
    return body;
}

HttpResponse HttpClient::Post(const std::wstring& host, int port, const std::wstring& path,
                               const std::string& body,
                               const std::map<std::string, std::string>& headers,
                               bool useHttps, int timeoutMs) {
    HttpResponse resp = {0, "", "", false};

    HINTERNET hSession = WinHttpOpen(L"BrowserAI/1.0",
        WINHTTP_ACCESS_TYPE_NO_PROXY,
        WINHTTP_NO_PROXY_NAME, WINHTTP_NO_PROXY_BYPASS, 0);
    if (!hSession) {
        resp.error = "Failed to create HTTP session";
        return resp;
    }

    HINTERNET hConnect = WinHttpConnect(hSession, host.c_str(),
        static_cast<INTERNET_PORT>(port), 0);
    if (!hConnect) {
        WinHttpCloseHandle(hSession);
        resp.error = "Failed to connect to " + WStringToString(host);
        return resp;
    }

    DWORD flags = useHttps ? WINHTTP_FLAG_SECURE : 0;
    HINTERNET hRequest = WinHttpOpenRequest(hConnect, L"POST", path.c_str(),
        nullptr, WINHTTP_NO_REFERER, WINHTTP_DEFAULT_ACCEPT_TYPES, flags);
    if (!hRequest) {
        WinHttpCloseHandle(hConnect);
        WinHttpCloseHandle(hSession);
        resp.error = "Failed to create request";
        return resp;
    }

    // Set timeouts
    DWORD timeout = static_cast<DWORD>(timeoutMs);
    WinHttpSetOption(hRequest, WINHTTP_OPTION_CONNECT_TIMEOUT, &timeout, sizeof(timeout));
    WinHttpSetOption(hRequest, WINHTTP_OPTION_SEND_TIMEOUT, &timeout, sizeof(timeout));
    WinHttpSetOption(hRequest, WINHTTP_OPTION_RECEIVE_TIMEOUT, &timeout, sizeof(timeout));

    // Build header string
    std::wstring headerStr;
    for (const auto& [key, val] : headers) {
        headerStr += StringToWString(key) + L": " + StringToWString(val) + L"\r\n";
    }
    headerStr += L"Content-Type: application/json\r\n";

    BOOL sent = WinHttpSendRequest(hRequest,
        headerStr.c_str(), static_cast<DWORD>(headerStr.length()),
        const_cast<char*>(body.c_str()), static_cast<DWORD>(body.size()),
        static_cast<DWORD>(body.size()), 0);

    if (!sent || !WinHttpReceiveResponse(hRequest, nullptr)) {
        DWORD err = GetLastError();
        WinHttpCloseHandle(hRequest);
        WinHttpCloseHandle(hConnect);
        WinHttpCloseHandle(hSession);
        resp.error = "HTTP request failed (error " + std::to_string(err) + ")";
        return resp;
    }

    // Get status code
    DWORD statusCode = 0;
    DWORD statusSize = sizeof(statusCode);
    WinHttpQueryHeaders(hRequest,
        WINHTTP_QUERY_STATUS_CODE | WINHTTP_QUERY_FLAG_NUMBER,
        WINHTTP_HEADER_NAME_BY_INDEX, &statusCode, &statusSize,
        WINHTTP_NO_HEADER_INDEX);
    resp.statusCode = static_cast<int>(statusCode);

    // Read body
    resp.body = ReadResponseBody(hRequest);

    WinHttpCloseHandle(hRequest);
    WinHttpCloseHandle(hConnect);
    WinHttpCloseHandle(hSession);

    resp.success = (resp.statusCode >= 200 && resp.statusCode < 300);
    if (!resp.success && resp.error.empty()) {
        resp.error = "HTTP " + std::to_string(resp.statusCode);
    }
    return resp;
}

HttpResponse HttpClient::Get(const std::wstring& host, int port, const std::wstring& path,
                              bool useHttps, int timeoutMs) {
    HttpResponse resp = {0, "", "", false};

    HINTERNET hSession = WinHttpOpen(L"BrowserAI/1.0",
        WINHTTP_ACCESS_TYPE_NO_PROXY,
        WINHTTP_NO_PROXY_NAME, WINHTTP_NO_PROXY_BYPASS, 0);
    if (!hSession) {
        resp.error = "Failed to create HTTP session";
        return resp;
    }

    HINTERNET hConnect = WinHttpConnect(hSession, host.c_str(),
        static_cast<INTERNET_PORT>(port), 0);
    if (!hConnect) {
        WinHttpCloseHandle(hSession);
        resp.error = "Failed to connect";
        return resp;
    }

    DWORD flags = useHttps ? WINHTTP_FLAG_SECURE : 0;
    HINTERNET hRequest = WinHttpOpenRequest(hConnect, L"GET", path.c_str(),
        nullptr, WINHTTP_NO_REFERER, WINHTTP_DEFAULT_ACCEPT_TYPES, flags);
    if (!hRequest) {
        WinHttpCloseHandle(hConnect);
        WinHttpCloseHandle(hSession);
        resp.error = "Failed to create request";
        return resp;
    }

    DWORD timeout = static_cast<DWORD>(timeoutMs);
    WinHttpSetOption(hRequest, WINHTTP_OPTION_CONNECT_TIMEOUT, &timeout, sizeof(timeout));
    WinHttpSetOption(hRequest, WINHTTP_OPTION_RECEIVE_TIMEOUT, &timeout, sizeof(timeout));

    BOOL sent = WinHttpSendRequest(hRequest, WINHTTP_NO_ADDITIONAL_HEADERS, 0,
        WINHTTP_NO_REQUEST_DATA, 0, 0, 0);

    if (!sent || !WinHttpReceiveResponse(hRequest, nullptr)) {
        WinHttpCloseHandle(hRequest);
        WinHttpCloseHandle(hConnect);
        WinHttpCloseHandle(hSession);
        resp.error = "HTTP GET request failed";
        return resp;
    }

    DWORD statusCode = 0;
    DWORD statusSize = sizeof(statusCode);
    WinHttpQueryHeaders(hRequest,
        WINHTTP_QUERY_STATUS_CODE | WINHTTP_QUERY_FLAG_NUMBER,
        WINHTTP_HEADER_NAME_BY_INDEX, &statusCode, &statusSize,
        WINHTTP_NO_HEADER_INDEX);
    resp.statusCode = static_cast<int>(statusCode);

    resp.body = ReadResponseBody(hRequest);

    WinHttpCloseHandle(hRequest);
    WinHttpCloseHandle(hConnect);
    WinHttpCloseHandle(hSession);

    resp.success = (resp.statusCode >= 200 && resp.statusCode < 300);
    return resp;
}
