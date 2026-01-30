#include "credential_store.h"
#include <wincred.h>

#pragma comment(lib, "Advapi32.lib")

std::wstring CredentialStore::MakeTarget(const std::string& provider) const {
    return L"BrowserAI:" + StringToWString(provider);
}

bool CredentialStore::StoreKey(const std::string& provider, const std::string& apiKey) {
    std::wstring target = MakeTarget(provider);

    CREDENTIALW cred = {};
    cred.Type = CRED_TYPE_GENERIC;
    cred.TargetName = const_cast<LPWSTR>(target.c_str());
    cred.CredentialBlobSize = static_cast<DWORD>(apiKey.size());
    cred.CredentialBlob = reinterpret_cast<LPBYTE>(const_cast<char*>(apiKey.data()));
    cred.Persist = CRED_PERSIST_LOCAL_MACHINE;

    std::wstring username = L"BrowserAI_" + StringToWString(provider);
    cred.UserName = const_cast<LPWSTR>(username.c_str());

    if (!CredWriteW(&cred, 0)) {
        LOG_ERROR(L"CredWriteW failed for " << target.c_str()
                  << L", error: " << GetLastError());
        return false;
    }

    LOG_INFO(L"Stored API key for " << StringToWString(provider).c_str());
    return true;
}

std::string CredentialStore::LoadKey(const std::string& provider) {
    std::wstring target = MakeTarget(provider);

    PCREDENTIALW pCred = nullptr;
    if (!CredReadW(target.c_str(), CRED_TYPE_GENERIC, 0, &pCred)) {
        return "";
    }

    std::string key(reinterpret_cast<char*>(pCred->CredentialBlob),
                    pCred->CredentialBlobSize);
    CredFree(pCred);
    return key;
}

bool CredentialStore::DeleteKey(const std::string& provider) {
    std::wstring target = MakeTarget(provider);
    if (!CredDeleteW(target.c_str(), CRED_TYPE_GENERIC, 0)) {
        DWORD err = GetLastError();
        if (err == ERROR_NOT_FOUND) {
            return true;  // Already gone
        }
        LOG_ERROR(L"CredDeleteW failed, error: " << err);
        return false;
    }
    return true;
}

bool CredentialStore::HasKey(const std::string& provider) {
    std::wstring target = MakeTarget(provider);
    PCREDENTIALW pCred = nullptr;
    if (!CredReadW(target.c_str(), CRED_TYPE_GENERIC, 0, &pCred)) {
        return false;
    }
    CredFree(pCred);
    return true;
}
