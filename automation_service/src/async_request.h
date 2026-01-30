#pragma once

#include "common.h"
#include <nlohmann/json.hpp>
#include <string>
#include <map>
#include <queue>
#include <mutex>
#include <thread>
#include <functional>
#include <atomic>
#include <condition_variable>
#include <chrono>
#include <random>

using json = nlohmann::json;

/**
 * Async Request Manager
 *
 * Manages background execution of long-running AI requests.
 * Single worker thread processes one request at a time.
 * Browser polls for results via request IDs.
 */
class AsyncRequestManager {
public:
    AsyncRequestManager();
    ~AsyncRequestManager();

    // Submit work. Returns a request_id immediately.
    std::string Submit(std::function<json()> work);

    // Poll for result. Returns status and result if complete.
    json Poll(const std::string& requestId);

    // Cancel a pending or in-progress request.
    json Cancel(const std::string& requestId);

    // Shut down the worker thread.
    void Shutdown();

private:
    struct Request {
        std::string id;
        std::string status;  // "queued", "processing", "complete", "error", "cancelled"
        json result;
        std::atomic<bool> cancelFlag{false};
        std::function<json()> work;
        std::chrono::steady_clock::time_point completedAt;
    };

    std::mutex mutex_;
    std::condition_variable cv_;
    std::map<std::string, std::shared_ptr<Request>> requests_;
    std::queue<std::shared_ptr<Request>> workQueue_;
    std::thread workerThread_;
    std::atomic<bool> running_{true};

    void WorkerLoop();
    void CleanupStale();
    std::string GenerateId();
};
