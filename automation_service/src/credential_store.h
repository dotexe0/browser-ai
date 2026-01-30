#pragma once

#include "common.h"
#include <string>

/**
 * Credential Store
 *
 * Wraps Windows Credential Manager (CredWrite/CredRead/CredDelete)
 * to securely store API keys for AI providers.
 * Keys are stored per-user, encrypted by the OS.
 */
class CredentialStore {
public:
    CredentialStore() = default;
    ~CredentialStore() = default;

    // Store an API key for a provider. Overwrites if exists.
    bool StoreKey(const std::string& provider, const std::string& apiKey);

    // Load an API key. Returns empty string if not found.
    std::string LoadKey(const std::string& provider);

    // Delete a stored key. Returns true if deleted or didn't exist.
    bool DeleteKey(const std::string& provider);

    // Check if a key exists for a provider.
    bool HasKey(const std::string& provider);

private:
    // Build the credential target name: "BrowserAI:<provider>"
    std::wstring MakeTarget(const std::string& provider) const;
};
