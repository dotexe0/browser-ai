#pragma once

#include "common.h"
#include <nlohmann/json.hpp>
#include <iostream>
#include <functional>

using json = nlohmann::json;

/**
 * Native Messaging Protocol Handler
 * 
 * Implements Chrome's Native Messaging protocol:
 * - Reads 4-byte length prefix from stdin
 * - Reads JSON message
 * - Processes and routes to handlers
 * - Writes response with 4-byte length prefix to stdout
 */
class NativeMessaging {
public:
    using MessageHandler = std::function<json(const json&)>;
    
    NativeMessaging();
    ~NativeMessaging();
    
    // Register a handler for an action
    void RegisterHandler(const std::string& action, MessageHandler handler);
    
    // Main message loop - reads from stdin, processes, writes to stdout
    void Run();
    
    // Send a message to browser (writes to stdout)
    static bool SendMessage(const json& message);
    
private:
    // Read a message from stdin
    static json ReadMessage();
    
    // Process a message and return response
    json ProcessMessage(const json& message);
    
    // Read exactly n bytes from stdin
    static bool ReadBytes(byte* buffer, size_t count);
    
    // Write bytes to stdout
    static bool WriteBytes(const byte* buffer, size_t count);
    
    // Map of action names to handlers
    std::map<std::string, MessageHandler> handlers_;
    
    // Whether to keep running
    bool running_;
};

