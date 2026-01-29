#include "chrome/browser/ui/webui/ai_panel/ai_panel_handler.h"

#include <windows.h>
#include <winhttp.h>
#include "base/functional/bind.h"
#include "base/values.h"

#pragma comment(lib, "winhttp.lib")

void AiPanelHandler::RegisterMessages() {
  web_ui()->RegisterMessageCallback(
      "ping",
      base::BindRepeating(&AiPanelHandler::HandlePing,
                          base::Unretained(this)));
  web_ui()->RegisterMessageCallback(
      "callBackend",
      base::BindRepeating(&AiPanelHandler::HandleCallBackend,
                          base::Unretained(this)));
  web_ui()->RegisterMessageCallback(
      "executeActions",
      base::BindRepeating(&AiPanelHandler::HandleExecuteActions,
                          base::Unretained(this)));
}

void AiPanelHandler::HandlePing(const base::Value::List& args) {
  AllowJavascript();
  FireWebUIListener("pong", base::Value("pong from C++"));
}

void AiPanelHandler::HandleCallBackend(const base::Value::List& args) {
  AllowJavascript();

  if (args.empty() || !args[0].is_string()) {
    FireWebUIListener("backendResponse",
                      base::Value("{\"error\":\"Invalid request\"}"));
    return;
  }

  const std::string& request_json = args[0].GetString();
  std::string response = HttpPost("/api/get-actions", request_json);

  FireWebUIListener("backendResponse", base::Value(response));
}

void AiPanelHandler::HandleExecuteActions(const base::Value::List& args) {
  AllowJavascript();

  if (args.empty() || !args[0].is_string()) {
    FireWebUIListener("executeResponse",
                      base::Value("{\"error\":\"Invalid request\"}"));
    return;
  }

  const std::string& request_json = args[0].GetString();
  std::string response = HttpPost("/api/get-actions", request_json);

  FireWebUIListener("executeResponse", base::Value(response));
}

std::string AiPanelHandler::HttpPost(const std::string& path,
                                      const std::string& json_body) {
  HINTERNET session = WinHttpOpen(L"BrowserAI/1.0",
                                   WINHTTP_ACCESS_TYPE_DEFAULT_PROXY,
                                   WINHTTP_NO_PROXY_NAME,
                                   WINHTTP_NO_PROXY_BYPASS, 0);
  if (!session)
    return "{\"error\":\"Failed to open HTTP session\"}";

  HINTERNET connection = WinHttpConnect(session, L"localhost",
                                         5000, 0);
  if (!connection) {
    WinHttpCloseHandle(session);
    return "{\"error\":\"Failed to connect to backend\"}";
  }

  std::wstring wide_path(path.begin(), path.end());
  HINTERNET request = WinHttpOpenRequest(connection, L"POST",
                                          wide_path.c_str(),
                                          nullptr, WINHTTP_NO_REFERER,
                                          WINHTTP_DEFAULT_ACCEPT_TYPES, 0);
  if (!request) {
    WinHttpCloseHandle(connection);
    WinHttpCloseHandle(session);
    return "{\"error\":\"Failed to create HTTP request\"}";
  }

  const wchar_t* headers = L"Content-Type: application/json\r\n";
  BOOL sent = WinHttpSendRequest(
      request, headers, -1L,
      (LPVOID)json_body.c_str(), json_body.size(),
      json_body.size(), 0);

  if (!sent || !WinHttpReceiveResponse(request, nullptr)) {
    WinHttpCloseHandle(request);
    WinHttpCloseHandle(connection);
    WinHttpCloseHandle(session);
    return "{\"error\":\"Backend not responding. Is server.py running?\"}";
  }

  // Read response
  std::string response;
  DWORD bytes_available = 0;
  do {
    WinHttpQueryDataAvailable(request, &bytes_available);
    if (bytes_available > 0) {
      std::vector<char> buffer(bytes_available + 1, 0);
      DWORD bytes_read = 0;
      WinHttpReadData(request, buffer.data(), bytes_available, &bytes_read);
      response.append(buffer.data(), bytes_read);
    }
  } while (bytes_available > 0);

  WinHttpCloseHandle(request);
  WinHttpCloseHandle(connection);
  WinHttpCloseHandle(session);

  return response.empty()
             ? "{\"error\":\"Empty response from backend\"}"
             : response;
}
