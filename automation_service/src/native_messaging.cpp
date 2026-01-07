#include "native_messaging.h"
#include <io.h>
#include <fcntl.h>

NativeMessaging::NativeMessaging() : running_(true) {
    // Set stdin/stdout to binary mode (Windows)
    _setmode(_fileno(stdin), _O_BINARY);
    _setmode(_fileno(stdout), _O_BINARY);
    
    // Disable buffering on stdout for immediate message delivery
    setvbuf(stdout, nullptr, _IONBF, 0);
    
    LOG_INFO(L"Native Messaging initialized");
}

NativeMessaging::~NativeMessaging() {
    LOG_INFO(L"Native Messaging shutting down");
}

void NativeMessaging::RegisterHandler(const std::string& action, MessageHandler handler) {
    handlers_[action] = handler;
    LOG_DEBUG(L"Registered handler for action: " << StringToWString(action).c_str());
}

void NativeMessaging::Run() {
    LOG_INFO(L"Native Messaging loop started");
    
    while (running_) {
        try {
            // Read message from browser
            json message = ReadMessage();
            
            if (message.is_null()) {
                // EOF or read error - browser disconnected
                LOG_INFO(L"Browser disconnected, exiting");
                break;
            }
            
            // Process message and get response
            json response = ProcessMessage(message);
            
            // Send response back to browser
            if (!SendMessage(response)) {
                LOG_ERROR(L"Failed to send response");
                break;
            }
            
        } catch (const std::exception& e) {
            LOG_ERROR(L"Error in message loop: " << StringToWString(e.what()).c_str());
            
            // Send error response
            json error_response = {
                {"success", false},
                {"error", e.what()}
            };
            SendMessage(error_response);
        }
    }
    
    LOG_INFO(L"Native Messaging loop ended");
}

json NativeMessaging::ReadMessage() {
    // Read 4-byte length prefix (little-endian)
    byte length_bytes[4];
    if (!ReadBytes(length_bytes, 4)) {
        return json(); // null = EOF
    }
    
    uint32_t length = 
        static_cast<uint32_t>(length_bytes[0]) |
        (static_cast<uint32_t>(length_bytes[1]) << 8) |
        (static_cast<uint32_t>(length_bytes[2]) << 16) |
        (static_cast<uint32_t>(length_bytes[3]) << 24);
    
    if (length == 0 || length > 1024 * 1024) { // Max 1MB
        throw std::runtime_error("Invalid message length");
    }
    
    // Read message content
    std::vector<byte> buffer(length);
    if (!ReadBytes(buffer.data(), length)) {
        throw std::runtime_error("Failed to read message content");
    }
    
    // Parse JSON
    std::string message_str(buffer.begin(), buffer.end());
    return json::parse(message_str);
}

bool NativeMessaging::SendMessage(const json& message) {
    // Serialize JSON
    std::string message_str = message.dump();
    uint32_t length = static_cast<uint32_t>(message_str.length());
    
    // Write 4-byte length prefix (little-endian)
    byte length_bytes[4] = {
        static_cast<byte>(length & 0xFF),
        static_cast<byte>((length >> 8) & 0xFF),
        static_cast<byte>((length >> 16) & 0xFF),
        static_cast<byte>((length >> 24) & 0xFF)
    };
    
    if (!WriteBytes(length_bytes, 4)) {
        return false;
    }
    
    // Write message content
    return WriteBytes(reinterpret_cast<const byte*>(message_str.c_str()), length);
}

json NativeMessaging::ProcessMessage(const json& message) {
    // Extract action from message
    if (!message.contains("action")) {
        return {
            {"success", false},
            {"error", "Missing 'action' field in message"}
        };
    }
    
    std::string action = message["action"];
    
    // Find handler
    auto it = handlers_.find(action);
    if (it == handlers_.end()) {
        return {
            {"success", false},
            {"error", "Unknown action: " + action}
        };
    }
    
    // Call handler
    try {
        return it->second(message);
    } catch (const std::exception& e) {
        return {
            {"success", false},
            {"error", std::string("Handler error: ") + e.what()}
        };
    }
}

bool NativeMessaging::ReadBytes(byte* buffer, size_t count) {
    size_t totalRead = 0;
    
    while (totalRead < count) {
        int result = _read(_fileno(stdin), buffer + totalRead, static_cast<unsigned int>(count - totalRead));
        
        if (result <= 0) {
            // EOF or error
            return false;
        }
        
        totalRead += result;
    }
    
    return true;
}

bool NativeMessaging::WriteBytes(const byte* buffer, size_t count) {
    size_t totalWritten = 0;
    
    while (totalWritten < count) {
        int result = _write(_fileno(stdout), buffer + totalWritten, static_cast<unsigned int>(count - totalWritten));
        
        if (result <= 0) {
            return false;
        }
        
        totalWritten += result;
    }
    
    return true;
}

