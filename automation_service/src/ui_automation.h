#pragma once

#include "common.h"
#include <UIAutomation.h>
#include <nlohmann/json.hpp>

using json = nlohmann::json;

/**
 * UI Automation Wrapper
 * 
 * Provides high-level interface to Windows UIAutomation API
 * for inspecting and interacting with UI elements.
 */
class UIAutomation {
public:
    UIAutomation();
    ~UIAutomation();
    
    // Initialize UIAutomation
    bool Initialize();
    
    // Get UI tree for desktop or specific window
    json GetUITree(HWND hwnd = nullptr);
    
    // Find element by automation ID, name, or class
    IUIAutomationElement* FindElement(const std::wstring& criteria);
    
    // Get element at specific point
    IUIAutomationElement* GetElementAt(int x, int y);
    
    // Get element properties
    json GetElementInfo(IUIAutomationElement* element);
    
    // Get interactive elements (buttons, textboxes, etc.)
    std::vector<UIElement> GetInteractiveElements(HWND hwnd = nullptr);
    
private:
    // Build UI tree recursively
    json BuildUITree(IUIAutomationElement* element, int maxDepth = 5, int currentDepth = 0);
    
    // Convert IUIAutomationElement to UIElement struct
    UIElement ElementToStruct(IUIAutomationElement* element);
    
    // Get element bounds
    Rect GetElementBounds(IUIAutomationElement* element);
    
    // Get element name
    std::wstring GetElementName(IUIAutomationElement* element);
    
    // Get element type/control type
    std::wstring GetElementType(IUIAutomationElement* element);
    
    // Get element class name
    std::wstring GetElementClassName(IUIAutomationElement* element);
    
    // Check if element is interactive
    bool IsInteractiveElement(IUIAutomationElement* element);
    
    // UIAutomation COM interface
    IUIAutomation* automation_;
    
    // COM initializer
    std::unique_ptr<ComInitializer> comInit_;
    
    // Whether initialized
    bool initialized_;
};

