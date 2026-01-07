#include "ui_automation.h"
#include <comdef.h>

UIAutomation::UIAutomation() : automation_(nullptr), initialized_(false) {
    comInit_ = std::make_unique<ComInitializer>();
}

UIAutomation::~UIAutomation() {
    if (automation_) {
        automation_->Release();
    }
}

bool UIAutomation::Initialize() {
    if (initialized_) {
        return true;
    }
    
    if (!comInit_->IsInitialized()) {
        LOG_ERROR(L"COM not initialized");
        return false;
    }
    
    HRESULT hr = CoCreateInstance(
        CLSID_CUIAutomation,
        nullptr,
        CLSCTX_INPROC_SERVER,
        IID_IUIAutomation,
        reinterpret_cast<void**>(&automation_)
    );
    
    if (FAILED(hr)) {
        LOG_ERROR(L"Failed to create UIAutomation instance");
        return false;
    }
    
    initialized_ = true;
    LOG_INFO(L"UIAutomation initialized successfully");
    return true;
}

json UIAutomation::GetUITree(HWND hwnd) {
    if (!initialized_) {
        throw std::runtime_error("UIAutomation not initialized");
    }
    
    IUIAutomationElement* rootElement = nullptr;
    HRESULT hr;
    
    if (hwnd) {
        // Get element for specific window
        hr = automation_->ElementFromHandle(hwnd, &rootElement);
    } else {
        // Get desktop root
        hr = automation_->GetRootElement(&rootElement);
    }
    
    if (FAILED(hr) || !rootElement) {
        throw std::runtime_error("Failed to get root element");
    }
    
    json tree = BuildUITree(rootElement);
    rootElement->Release();
    
    return tree;
}

json UIAutomation::BuildUITree(IUIAutomationElement* element, int maxDepth, int currentDepth) {
    if (!element || currentDepth >= maxDepth) {
        return json::object();
    }
    
    json node;
    node["name"] = WStringToString(GetElementName(element));
    node["type"] = WStringToString(GetElementType(element));
    node["className"] = WStringToString(GetElementClassName(element));
    
    Rect bounds = GetElementBounds(element);
    node["bounds"] = {
        {"x", bounds.x},
        {"y", bounds.y},
        {"width", bounds.width},
        {"height", bounds.height}
    };
    
    BOOL enabled = FALSE;
    element->get_CurrentIsEnabled(&enabled);
    node["enabled"] = enabled != FALSE;
    
    // Get children
    IUIAutomationElementArray* children = nullptr;
    IUIAutomationCondition* condition = nullptr;
    automation_->CreateTrueCondition(&condition);
    
    HRESULT hr = element->FindAll(TreeScope_Children, condition, &children);
    
    if (SUCCEEDED(hr) && children) {
        int childCount = 0;
        children->get_Length(&childCount);
        
        if (childCount > 0 && childCount < 100) { // Limit children
            json childArray = json::array();
            
            for (int i = 0; i < std::min(childCount, 20); i++) { // Max 20 children per level
                IUIAutomationElement* child = nullptr;
                hr = children->GetElement(i, &child);
                
                if (SUCCEEDED(hr) && child) {
                    childArray.push_back(BuildUITree(child, maxDepth, currentDepth + 1));
                    child->Release();
                }
            }
            
            node["children"] = childArray;
        }
        
        children->Release();
    }
    
    if (condition) {
        condition->Release();
    }
    
    return node;
}

Rect UIAutomation::GetElementBounds(IUIAutomationElement* element) {
    Rect rect = {0, 0, 0, 0};
    
    if (!element) {
        return rect;
    }
    
    RECT boundingRect;
    HRESULT hr = element->get_CurrentBoundingRectangle(&boundingRect);
    
    if (SUCCEEDED(hr)) {
        rect.x = boundingRect.left;
        rect.y = boundingRect.top;
        rect.width = boundingRect.right - boundingRect.left;
        rect.height = boundingRect.bottom - boundingRect.top;
    }
    
    return rect;
}

std::wstring UIAutomation::GetElementName(IUIAutomationElement* element) {
    if (!element) {
        return L"";
    }
    
    BSTR name = nullptr;
    HRESULT hr = element->get_CurrentName(&name);
    
    std::wstring result;
    if (SUCCEEDED(hr) && name) {
        result = name;
        SysFreeString(name);
    }
    
    return result;
}

std::wstring UIAutomation::GetElementType(IUIAutomationElement* element) {
    if (!element) {
        return L"";
    }
    
    CONTROLTYPEID controlType;
    HRESULT hr = element->get_CurrentControlType(&controlType);
    
    if (FAILED(hr)) {
        return L"Unknown";
    }
    
    // Map control type IDs to names
    switch (controlType) {
        case UIA_ButtonControlTypeId: return L"Button";
        case UIA_CalendarControlTypeId: return L"Calendar";
        case UIA_CheckBoxControlTypeId: return L"CheckBox";
        case UIA_ComboBoxControlTypeId: return L"ComboBox";
        case UIA_EditControlTypeId: return L"Edit";
        case UIA_HyperlinkControlTypeId: return L"Hyperlink";
        case UIA_ImageControlTypeId: return L"Image";
        case UIA_ListItemControlTypeId: return L"ListItem";
        case UIA_ListControlTypeId: return L"List";
        case UIA_MenuControlTypeId: return L"Menu";
        case UIA_MenuBarControlTypeId: return L"MenuBar";
        case UIA_MenuItemControlTypeId: return L"MenuItem";
        case UIA_ProgressBarControlTypeId: return L"ProgressBar";
        case UIA_RadioButtonControlTypeId: return L"RadioButton";
        case UIA_ScrollBarControlTypeId: return L"ScrollBar";
        case UIA_SliderControlTypeId: return L"Slider";
        case UIA_SpinnerControlTypeId: return L"Spinner";
        case UIA_StatusBarControlTypeId: return L"StatusBar";
        case UIA_TabControlTypeId: return L"Tab";
        case UIA_TabItemControlTypeId: return L"TabItem";
        case UIA_TextControlTypeId: return L"Text";
        case UIA_ToolBarControlTypeId: return L"ToolBar";
        case UIA_ToolTipControlTypeId: return L"ToolTip";
        case UIA_TreeControlTypeId: return L"Tree";
        case UIA_TreeItemControlTypeId: return L"TreeItem";
        case UIA_CustomControlTypeId: return L"Custom";
        case UIA_GroupControlTypeId: return L"Group";
        case UIA_ThumbControlTypeId: return L"Thumb";
        case UIA_DataGridControlTypeId: return L"DataGrid";
        case UIA_DataItemControlTypeId: return L"DataItem";
        case UIA_DocumentControlTypeId: return L"Document";
        case UIA_SplitButtonControlTypeId: return L"SplitButton";
        case UIA_WindowControlTypeId: return L"Window";
        case UIA_PaneControlTypeId: return L"Pane";
        case UIA_HeaderControlTypeId: return L"Header";
        case UIA_HeaderItemControlTypeId: return L"HeaderItem";
        case UIA_TableControlTypeId: return L"Table";
        case UIA_TitleBarControlTypeId: return L"TitleBar";
        case UIA_SeparatorControlTypeId: return L"Separator";
        default: return L"Unknown";
    }
}

std::wstring UIAutomation::GetElementClassName(IUIAutomationElement* element) {
    if (!element) {
        return L"";
    }
    
    BSTR className = nullptr;
    HRESULT hr = element->get_CurrentClassName(&className);
    
    std::wstring result;
    if (SUCCEEDED(hr) && className) {
        result = className;
        SysFreeString(className);
    }
    
    return result;
}

IUIAutomationElement* UIAutomation::GetElementAt(int x, int y) {
    if (!initialized_) {
        return nullptr;
    }
    
    POINT pt = {x, y};
    IUIAutomationElement* element = nullptr;
    
    HRESULT hr = automation_->ElementFromPoint(pt, &element);
    
    if (FAILED(hr)) {
        return nullptr;
    }
    
    return element;
}

json UIAutomation::GetElementInfo(IUIAutomationElement* element) {
    if (!element) {
        return json::object();
    }
    
    json info;
    info["name"] = WStringToString(GetElementName(element));
    info["type"] = WStringToString(GetElementType(element));
    info["className"] = WStringToString(GetElementClassName(element));
    
    Rect bounds = GetElementBounds(element);
    info["bounds"] = {
        {"x", bounds.x},
        {"y", bounds.y},
        {"width", bounds.width},
        {"height", bounds.height}
    };
    
    BOOL enabled = FALSE;
    element->get_CurrentIsEnabled(&enabled);
    info["enabled"] = enabled != FALSE;
    
    return info;
}

std::vector<UIElement> UIAutomation::GetInteractiveElements(HWND hwnd) {
    std::vector<UIElement> elements;
    
    // This is a simplified version - real implementation would
    // traverse the tree and collect interactive elements
    // For now, return empty vector
    
    return elements;
}

