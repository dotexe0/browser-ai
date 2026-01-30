cmake_minimum_required(VERSION 3.20)
project(BrowserAIAutomationService VERSION 1.0.0 LANGUAGES CXX)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Add compile options
if(MSVC)
    add_compile_options(/W4 /WX- /permissive-)
    add_definitions(-D_CRT_SECURE_NO_WARNINGS)
    add_definitions(-DUNICODE -D_UNICODE)
else()
    add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Include directories
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/src)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/include)

# Third-party: JSON library (nlohmann/json - header-only)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/third_party)

# Source files
set(SOURCES
    src/main.cpp
    src/native_messaging.cpp
    src/ui_automation.cpp
    src/screen_capture.cpp
    src/input_controller.cpp
    src/action_executor.cpp
    src/credential_store.cpp
    src/http_client.cpp
    src/ai_provider.cpp
    src/async_request.cpp
)

# Header files
set(HEADERS
    src/native_messaging.h
    src/ui_automation.h
    src/screen_capture.h
    src/input_controller.h
    src/action_executor.h
    src/credential_store.h
    src/http_client.h
    src/ai_provider.h
    src/async_request.h
    src/common.h
)

# Create executable
add_executable(automation_service ${SOURCES} ${HEADERS})

# Link Windows libraries
target_link_libraries(automation_service
    UIAutomationCore    # For UIAutomation API
    D3D11               # For Desktop Duplication API
    DXGI                # For DXGI
    User32              # For SendInput
    windowscodecs       # For WIC (image encoding)
    Ole32               # For COM
    OleAut32            # For COM automation
    Winhttp             # For HTTP client (local LLM detection)
    Advapi32            # For Windows Credential Manager
)

# Set output directory
set_target_properties(automation_service PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin
)

# For production: Enable UIAccess (requires code signing)
# set_target_properties(automation_service PROPERTIES
#     LINK_FLAGS "/MANIFESTUAC:level='asInvoker' uiAccess='true'"
# )

# Install target
install(TARGETS automation_service
    RUNTIME DESTINATION bin
)

# Copy manifest for Native Messaging registration
configure_file(
    ${CMAKE_CURRENT_SOURCE_DIR}/manifest.json.in
    ${CMAKE_BINARY_DIR}/bin/manifest.json
    @ONLY
)

