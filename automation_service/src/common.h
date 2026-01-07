#pragma once

#define NOMINMAX  // Prevent Windows.h from defining min/max macros

#include <string>
#include <vector>
#include <memory>
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <algorithm>
#include <windows.h>

// Common types
using byte = uint8_t;
using ImageData = std::vector<byte>;

// Rectangle structure
struct Rect {
    int x;
    int y;
    int width;
    int height;
};

// UI Element information
struct UIElement {
    std::wstring id;
    std::wstring name;
    std::wstring type;
    std::wstring className;
    Rect bounds;
    bool enabled;
    bool visible;
    std::vector<UIElement> children;
};

// Action types
enum class ActionType {
    Click,
    DoubleClick,
    RightClick,
    Type,
    PressKeys,
    Scroll,
    Wait,
    MoveMouse,
    Drag,
    Unknown
};

// Button types for clicks
enum class MouseButton {
    Left,
    Right,
    Middle
};

// Logging macros
#define LOG_INFO(msg) std::wcerr << L"[INFO] " << msg << std::endl
#define LOG_ERROR(msg) std::wcerr << L"[ERROR] " << msg << std::endl
#define LOG_DEBUG(msg) std::wcerr << L"[DEBUG] " << msg << std::endl

// Helper functions
inline std::wstring StringToWString(const std::string& str) {
    if (str.empty()) return std::wstring();
    int size = MultiByteToWideChar(CP_UTF8, 0, str.c_str(), -1, nullptr, 0);
    std::wstring result(size - 1, 0);
    MultiByteToWideChar(CP_UTF8, 0, str.c_str(), -1, &result[0], size);
    return result;
}

inline std::string WStringToString(const std::wstring& wstr) {
    if (wstr.empty()) return std::string();
    int size = WideCharToMultiByte(CP_UTF8, 0, wstr.c_str(), -1, nullptr, 0, nullptr, nullptr);
    std::string result(size - 1, 0);
    WideCharToMultiByte(CP_UTF8, 0, wstr.c_str(), -1, &result[0], size, nullptr, nullptr);
    return result;
}

// COM initialization helper
class ComInitializer {
public:
    ComInitializer() {
        hr = CoInitializeEx(nullptr, COINIT_APARTMENTTHREADED);
        initialized = SUCCEEDED(hr);
    }
    
    ~ComInitializer() {
        if (initialized) {
            CoUninitialize();
        }
    }
    
    bool IsInitialized() const { return initialized; }
    HRESULT GetResult() const { return hr; }
    
private:
    HRESULT hr;
    bool initialized;
};

