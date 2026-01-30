#pragma once

#include "common.h"
#include <vector>

/**
 * Input Controller using SendInput API
 * 
 * Provides mouse and keyboard input injection.
 */
class InputController {
public:
    InputController();
    ~InputController();
    
    // Mouse operations
    void MoveMouse(int x, int y);
    void Click(int x, int y, MouseButton button = MouseButton::Left);
    void DoubleClick(int x, int y, MouseButton button = MouseButton::Left);
    void RightClick(int x, int y);
    void Drag(int startX, int startY, int endX, int endY);
    void Scroll(int delta, int x = -1, int y = -1);
    
    // Keyboard operations
    void TypeText(const std::wstring& text);
    void PressKey(WORD virtualKey, bool down);
    void PressKeys(const std::vector<WORD>& keys);
    
    // Utility
    void Wait(int milliseconds);
    
private:
    bool ValidateCoordinates(int x, int y) const;

    // Convert screen coordinates to absolute coordinates for SendInput
    void ScreenToAbsolute(int& x, int& y);
    
    // Send mouse event
    void SendMouseEvent(DWORD flags, int x = 0, int y = 0, DWORD data = 0);
    
    // Send keyboard event
    void SendKeyEvent(WORD virtualKey, bool keyDown);
    
    // Screen dimensions
    int screenWidth_;
    int screenHeight_;
};

