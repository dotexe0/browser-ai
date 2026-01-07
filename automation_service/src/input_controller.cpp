#include "input_controller.h"
#include <thread>
#include <chrono>

InputController::InputController() {
    screenWidth_ = GetSystemMetrics(SM_CXSCREEN);
    screenHeight_ = GetSystemMetrics(SM_CYSCREEN);
}

InputController::~InputController() {
}

void InputController::ScreenToAbsolute(int& x, int& y) {
    // Convert screen coordinates to absolute (0-65535 range)
    x = (x * 65535) / screenWidth_;
    y = (y * 65535) / screenHeight_;
}

void InputController::SendMouseEvent(DWORD flags, int x, int y, DWORD data) {
    INPUT input = {};
    input.type = INPUT_MOUSE;
    input.mi.dwFlags = flags;
    input.mi.dx = x;
    input.mi.dy = y;
    input.mi.mouseData = data;
    
    SendInput(1, &input, sizeof(INPUT));
}

void InputController::MoveMouse(int x, int y) {
    int absX = x, absY = y;
    ScreenToAbsolute(absX, absY);
    
    SendMouseEvent(MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE, absX, absY);
    
    // Small delay to ensure movement completes
    std::this_thread::sleep_for(std::chrono::milliseconds(10));
}

void InputController::Click(int x, int y, MouseButton button) {
    // Move to position
    MoveMouse(x, y);
    
    // Determine button flags
    DWORD downFlag, upFlag;
    
    switch (button) {
        case MouseButton::Left:
            downFlag = MOUSEEVENTF_LEFTDOWN;
            upFlag = MOUSEEVENTF_LEFTUP;
            break;
        case MouseButton::Right:
            downFlag = MOUSEEVENTF_RIGHTDOWN;
            upFlag = MOUSEEVENTF_RIGHTUP;
            break;
        case MouseButton::Middle:
            downFlag = MOUSEEVENTF_MIDDLEDOWN;
            upFlag = MOUSEEVENTF_MIDDLEUP;
            break;
        default:
            return;
    }
    
    int absX = x, absY = y;
    ScreenToAbsolute(absX, absY);
    
    // Click down
    SendMouseEvent(downFlag | MOUSEEVENTF_ABSOLUTE, absX, absY);
    std::this_thread::sleep_for(std::chrono::milliseconds(50));
    
    // Click up
    SendMouseEvent(upFlag | MOUSEEVENTF_ABSOLUTE, absX, absY);
    std::this_thread::sleep_for(std::chrono::milliseconds(50));
}

void InputController::DoubleClick(int x, int y, MouseButton button) {
    Click(x, y, button);
    std::this_thread::sleep_for(std::chrono::milliseconds(50));
    Click(x, y, button);
}

void InputController::RightClick(int x, int y) {
    Click(x, y, MouseButton::Right);
}

void InputController::Drag(int startX, int startY, int endX, int endY) {
    // Move to start position
    MoveMouse(startX, startY);
    std::this_thread::sleep_for(std::chrono::milliseconds(100));
    
    int absX = startX, absY = startY;
    ScreenToAbsolute(absX, absY);
    
    // Press left button
    SendMouseEvent(MOUSEEVENTF_LEFTDOWN | MOUSEEVENTF_ABSOLUTE, absX, absY);
    std::this_thread::sleep_for(std::chrono::milliseconds(100));
    
    // Move to end position
    MoveMouse(endX, endY);
    std::this_thread::sleep_for(std::chrono::milliseconds(100));
    
    absX = endX;
    absY = endY;
    ScreenToAbsolute(absX, absY);
    
    // Release left button
    SendMouseEvent(MOUSEEVENTF_LEFTUP | MOUSEEVENTF_ABSOLUTE, absX, absY);
}

void InputController::Scroll(int delta, int x, int y) {
    if (x >= 0 && y >= 0) {
        MoveMouse(x, y);
    }
    
    // Scroll wheel (delta is in WHEEL_DELTA units, typically 120)
    SendMouseEvent(MOUSEEVENTF_WHEEL, 0, 0, delta * WHEEL_DELTA);
    std::this_thread::sleep_for(std::chrono::milliseconds(50));
}

void InputController::SendKeyEvent(WORD virtualKey, bool keyDown) {
    INPUT input = {};
    input.type = INPUT_KEYBOARD;
    input.ki.wVk = virtualKey;
    input.ki.dwFlags = keyDown ? 0 : KEYEVENTF_KEYUP;
    
    SendInput(1, &input, sizeof(INPUT));
}

void InputController::PressKey(WORD virtualKey, bool down) {
    SendKeyEvent(virtualKey, down);
    std::this_thread::sleep_for(std::chrono::milliseconds(10));
}

void InputController::TypeText(const std::wstring& text) {
    for (wchar_t ch : text) {
        // Handle special characters as virtual keys
        if (ch == L'\n' || ch == L'\r') {
            // Newline: press Enter key
            PressKey(VK_RETURN, true);
            PressKey(VK_RETURN, false);
            std::this_thread::sleep_for(std::chrono::milliseconds(20));
        } else if (ch == L'\t') {
            // Tab: press Tab key
            PressKey(VK_TAB, true);
            PressKey(VK_TAB, false);
            std::this_thread::sleep_for(std::chrono::milliseconds(20));
        } else {
            // Regular character: use Unicode input
            INPUT input = {};
            input.type = INPUT_KEYBOARD;
            input.ki.wScan = ch;
            input.ki.dwFlags = KEYEVENTF_UNICODE;
            
            // Key down
            SendInput(1, &input, sizeof(INPUT));
            
            // Key up
            input.ki.dwFlags = KEYEVENTF_UNICODE | KEYEVENTF_KEYUP;
            SendInput(1, &input, sizeof(INPUT));
            
            std::this_thread::sleep_for(std::chrono::milliseconds(20));
        }
    }
}

void InputController::PressKeys(const std::vector<WORD>& keys) {
    // Press all keys down
    for (WORD key : keys) {
        PressKey(key, true);
    }
    
    std::this_thread::sleep_for(std::chrono::milliseconds(50));
    
    // Release all keys (in reverse order)
    for (auto it = keys.rbegin(); it != keys.rend(); ++it) {
        PressKey(*it, false);
    }
}

void InputController::Wait(int milliseconds) {
    std::this_thread::sleep_for(std::chrono::milliseconds(milliseconds));
}

