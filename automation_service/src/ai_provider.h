#pragma once

#include "common.h"
#include "http_client.h"
#include "credential_store.h"
#include <nlohmann/json.hpp>
#include <string>

using json = nlohmann::json;

/**
 * AI Provider
 *
 * Routes AI requests to OpenAI, Anthropic, or Ollama.
 * Owns the system prompt, builds provider-specific payloads,
 * and parses AI text responses into action arrays.
 */
class AIProvider {
public:
    AIProvider(CredentialStore& credStore);
    ~AIProvider() = default;

    // Main entry point: get actions from an AI provider.
    // screenshotBase64 and uiTree are captured internally by caller.
    json GetActions(const std::string& provider,
                    const std::string& screenshotBase64,
                    const json& uiTree,
                    const std::string& userRequest);

    // Get status of all providers (which have keys configured, which are available)
    json GetProviderStatus();

private:
    CredentialStore& credStore_;
    HttpClient http_;

    json CallOpenAI(const std::string& apiKey,
                    const std::string& screenshot,
                    const json& uiTree,
                    const std::string& request);

    json CallAnthropic(const std::string& apiKey,
                       const std::string& screenshot,
                       const json& uiTree,
                       const std::string& request);

    json CallOllama(const std::string& screenshot,
                    const json& uiTree,
                    const std::string& request);

    // Parse AI text response into validated action array.
    // Strips markdown fences, parses JSON, validates each action.
    json ParseActionsFromResponse(const std::string& responseText);

    // Validate a single action (bounds, types, limits)
    bool ValidateAction(const json& action);

    // The system prompt shared by all providers
    static const std::string SYSTEM_PROMPT;
};
