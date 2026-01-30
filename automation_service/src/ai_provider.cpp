#include "ai_provider.h"
#include <sstream>
#include <algorithm>
#include <set>

const std::string AIProvider::SYSTEM_PROMPT = R"(You are a desktop automation assistant. Analyze the screenshot and UI tree, then return a JSON array of actions to accomplish the user's request.

Available actions:
- click: {"action": "click", "params": {"x": 100, "y": 200}, "confidence": 0.9}
- type: {"action": "type", "params": {"text": "hello"}, "confidence": 0.9}
- press_keys: {"action": "press_keys", "params": {"keys": ["ctrl", "s"]}, "confidence": 0.9}
- scroll: {"action": "scroll", "params": {"delta": -3, "x": 500, "y": 400}, "confidence": 0.9}
- wait: {"action": "wait", "params": {"ms": 1000}, "confidence": 0.9}

UI TREE USAGE:
- Search for elements by name/type in the UI tree
- Use element 'bounds' {x, y, width, height} to calculate click coordinates
- Click center of element: x + width/2, y + height/2

Return ONLY a JSON array of actions. No explanations or other text.)";


AIProvider::AIProvider(CredentialStore& credStore)
    : credStore_(credStore) {}


json AIProvider::GetActions(const std::string& provider,
                            const std::string& screenshotBase64,
                            const json& uiTree,
                            const std::string& userRequest) {
    if (provider == "openai") {
        std::string key = credStore_.LoadKey("openai");
        if (key.empty()) {
            return {{"success", false}, {"error", "OpenAI API key not configured. Add via Settings."}};
        }
        return CallOpenAI(key, screenshotBase64, uiTree, userRequest);
    }

    if (provider == "anthropic") {
        std::string key = credStore_.LoadKey("anthropic");
        if (key.empty()) {
            return {{"success", false}, {"error", "Anthropic API key not configured. Add via Settings."}};
        }
        return CallAnthropic(key, screenshotBase64, uiTree, userRequest);
    }

    if (provider == "ollama") {
        return CallOllama(screenshotBase64, uiTree, userRequest);
    }

    return {{"success", false}, {"error", "Unknown provider: " + provider}};
}


json AIProvider::GetProviderStatus() {
    // Check Ollama availability via HTTP GET
    HttpResponse ollamaResp = http_.Get(L"localhost", 11434, L"/api/tags");

    return {
        {"success", true},
        {"providers", {
            {"openai", {
                {"has_key", credStore_.HasKey("openai")},
                {"type", "cloud"}
            }},
            {"anthropic", {
                {"has_key", credStore_.HasKey("anthropic")},
                {"type", "cloud"}
            }},
            {"ollama", {
                {"has_key", false},
                {"type", "local"},
                {"available", ollamaResp.success}
            }}
        }}
    };
}


json AIProvider::CallOpenAI(const std::string& apiKey,
                             const std::string& screenshot,
                             const json& uiTree,
                             const std::string& request) {
    json payload = {
        {"model", "gpt-4o"},
        {"max_tokens", 1000},
        {"messages", json::array({
            {{"role", "system"}, {"content", SYSTEM_PROMPT}},
            {{"role", "user"}, {"content", json::array({
                {{"type", "text"},
                 {"text", "User request: " + request + "\n\nUI Tree: " + uiTree.dump(2)}},
                {{"type", "image_url"},
                 {"image_url", {{"url", "data:image/png;base64," + screenshot}}}}
            })}}
        })}
    };

    std::map<std::string, std::string> headers = {
        {"Authorization", "Bearer " + apiKey}
    };

    HttpResponse resp = http_.Post(L"api.openai.com", 443,
        L"/v1/chat/completions", payload.dump(), headers, true);

    if (!resp.success) {
        std::string errMsg = "OpenAI API error: " + resp.error;
        if (resp.statusCode == 401) errMsg = "Invalid OpenAI API key. Update via Settings.";
        if (resp.statusCode == 429) errMsg = "OpenAI rate limit exceeded. Try again later.";
        return {{"success", false}, {"error", errMsg}};
    }

    try {
        json result = json::parse(resp.body);
        std::string content = result["choices"][0]["message"]["content"];
        return ParseActionsFromResponse(content);
    } catch (const std::exception& e) {
        return {{"success", false}, {"error", std::string("Failed to parse OpenAI response: ") + e.what()}};
    }
}


json AIProvider::CallAnthropic(const std::string& apiKey,
                                const std::string& screenshot,
                                const json& uiTree,
                                const std::string& request) {
    json payload = {
        {"model", "claude-sonnet-4-20250514"},
        {"max_tokens", 1024},
        {"messages", json::array({
            {{"role", "user"}, {"content", json::array({
                {{"type", "image"},
                 {"source", {{"type", "base64"}, {"media_type", "image/png"}, {"data", screenshot}}}},
                {{"type", "text"},
                 {"text", SYSTEM_PROMPT + "\n\nUser request: " + request + "\n\nUI Tree: " + uiTree.dump()}}
            })}}
        })}
    };

    std::map<std::string, std::string> headers = {
        {"x-api-key", apiKey},
        {"anthropic-version", "2023-06-01"}
    };

    HttpResponse resp = http_.Post(L"api.anthropic.com", 443,
        L"/v1/messages", payload.dump(), headers, true);

    if (!resp.success) {
        std::string errMsg = "Anthropic API error: " + resp.error;
        if (resp.statusCode == 401) errMsg = "Invalid Anthropic API key. Update via Settings.";
        if (resp.statusCode == 429) errMsg = "Anthropic rate limit exceeded. Try again later.";
        return {{"success", false}, {"error", errMsg}};
    }

    try {
        json result = json::parse(resp.body);
        std::string content = result["content"][0]["text"];
        return ParseActionsFromResponse(content);
    } catch (const std::exception& e) {
        return {{"success", false}, {"error", std::string("Failed to parse Anthropic response: ") + e.what()}};
    }
}


json AIProvider::CallOllama(const std::string& screenshot,
                             const json& uiTree,
                             const std::string& request) {
    std::string prompt = SYSTEM_PROMPT + "\n\nUser request: " + request
                         + "\n\nUI Tree:\n" + uiTree.dump(2);

    json payload = {
        {"model", "llava"},
        {"prompt", prompt},
        {"stream", false}
    };

    if (!screenshot.empty()) {
        payload["images"] = json::array({screenshot});
    }

    HttpResponse resp = http_.Post(L"localhost", 11434,
        L"/api/generate", payload.dump(), {}, false, 120000);  // 2min timeout for local inference

    if (!resp.success) {
        return {{"success", false},
                {"error", "Ollama error: " + resp.error + ". Is Ollama running?"}};
    }

    try {
        json result = json::parse(resp.body);
        std::string content = result.value("response", "");
        return ParseActionsFromResponse(content);
    } catch (const std::exception& e) {
        return {{"success", false}, {"error", std::string("Failed to parse Ollama response: ") + e.what()}};
    }
}


json AIProvider::ParseActionsFromResponse(const std::string& responseText) {
    std::string text = responseText;

    // Trim whitespace
    auto ltrim = text.find_first_not_of(" \t\n\r");
    if (ltrim != std::string::npos) text = text.substr(ltrim);
    auto rtrim = text.find_last_not_of(" \t\n\r");
    if (rtrim != std::string::npos) text = text.substr(0, rtrim + 1);

    // Strip markdown code fences
    if (text.rfind("```", 0) == 0) {
        auto firstNewline = text.find('\n');
        if (firstNewline != std::string::npos) {
            text = text.substr(firstNewline + 1);
        }
        auto lastFence = text.rfind("```");
        if (lastFence != std::string::npos) {
            text = text.substr(0, lastFence);
        }
        // Trim again
        ltrim = text.find_first_not_of(" \t\n\r");
        if (ltrim != std::string::npos) text = text.substr(ltrim);
        rtrim = text.find_last_not_of(" \t\n\r");
        if (rtrim != std::string::npos) text = text.substr(0, rtrim + 1);
    }

    // Parse JSON
    json actions;
    try {
        actions = json::parse(text);
    } catch (...) {
        return {{"success", false},
                {"error", "AI did not return valid JSON"},
                {"raw_response", responseText}};
    }

    if (!actions.is_array()) {
        return {{"success", false},
                {"error", "AI response is not an array of actions"},
                {"raw_response", responseText}};
    }

    // Validate each action
    json validated = json::array();
    static const std::set<std::string> validTypes = {"click", "type", "scroll", "press_keys", "wait"};

    for (const auto& action : actions) {
        if (!action.is_object()) continue;
        if (!action.contains("action")) continue;
        std::string type = action["action"];
        if (validTypes.find(type) == validTypes.end()) continue;
        if (!ValidateAction(action)) continue;

        // Add default confidence if missing
        json validated_action = action;
        if (!validated_action.contains("confidence")) {
            validated_action["confidence"] = 0.7;
        }
        validated.push_back(validated_action);
    }

    if (validated.empty()) {
        return {{"success", false},
                {"error", "AI returned no valid actions"},
                {"raw_response", responseText}};
    }

    return {{"success", true}, {"actions", validated}};
}


bool AIProvider::ValidateAction(const json& action) {
    std::string type = action["action"];
    json params = action.value("params", json::object());

    if (type == "click") {
        if (!params.contains("x") || !params.contains("y")) return false;
        auto x = params["x"];
        auto y = params["y"];
        if (!x.is_number() || !y.is_number()) return false;
        if (x.get<double>() < 0 || x.get<double>() > 10000) return false;
        if (y.get<double>() < 0 || y.get<double>() > 10000) return false;
    }

    if (type == "type") {
        if (!params.contains("text")) return false;
        if (!params["text"].is_string()) return false;
        std::string text = params["text"];
        if (text.empty() || text.length() > 10000) return false;
    }

    if (type == "wait") {
        if (!params.contains("ms")) return false;
        if (!params["ms"].is_number()) return false;
        double ms = params["ms"].get<double>();
        if (ms < 0 || ms > 30000) return false;
    }

    if (type == "scroll") {
        if (!params.contains("delta")) return false;
        if (!params["delta"].is_number()) return false;
    }

    if (type == "press_keys") {
        if (!params.contains("keys")) return false;
        if (!params["keys"].is_array() || params["keys"].empty()) return false;
    }

    return true;
}
