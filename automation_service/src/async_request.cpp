#include "async_request.h"
#include <sstream>
#include <iomanip>

AsyncRequestManager::AsyncRequestManager() {
    workerThread_ = std::thread(&AsyncRequestManager::WorkerLoop, this);
}

AsyncRequestManager::~AsyncRequestManager() {
    Shutdown();
}

void AsyncRequestManager::Shutdown() {
    running_ = false;
    cv_.notify_all();
    if (workerThread_.joinable()) {
        workerThread_.join();
    }
}

std::string AsyncRequestManager::GenerateId() {
    static std::mt19937 rng(std::random_device{}());
    static const char chars[] = "abcdefghijklmnopqrstuvwxyz0123456789";
    std::string id;
    id.reserve(8);
    for (int i = 0; i < 8; ++i) {
        id += chars[rng() % (sizeof(chars) - 1)];
    }
    return id;
}

std::string AsyncRequestManager::Submit(std::function<json()> work) {
    std::lock_guard<std::mutex> lock(mutex_);

    CleanupStale();

    auto req = std::make_shared<Request>();
    req->id = GenerateId();
    req->status = "queued";
    req->work = std::move(work);

    requests_[req->id] = req;
    workQueue_.push(req);
    cv_.notify_one();

    return req->id;
}

json AsyncRequestManager::Poll(const std::string& requestId) {
    std::lock_guard<std::mutex> lock(mutex_);

    auto it = requests_.find(requestId);
    if (it == requests_.end()) {
        return {{"request_id", requestId}, {"status", "not_found"}};
    }

    auto& req = it->second;
    json response = {{"request_id", requestId}, {"status", req->status}};

    if (req->status == "complete" || req->status == "error") {
        response["result"] = req->result;
        // Merge actions into top level for convenience
        if (req->result.contains("actions")) {
            response["actions"] = req->result["actions"];
        }
        if (req->result.contains("error")) {
            response["error"] = req->result["error"];
        }
    }

    return response;
}

json AsyncRequestManager::Cancel(const std::string& requestId) {
    std::lock_guard<std::mutex> lock(mutex_);

    auto it = requests_.find(requestId);
    if (it == requests_.end()) {
        return {{"request_id", requestId}, {"status", "not_found"}};
    }

    auto& req = it->second;
    if (req->status == "queued") {
        req->status = "cancelled";
    } else if (req->status == "processing") {
        req->cancelFlag = true;
        // Worker will check the flag and discard result
    }
    // If already complete/error/cancelled, no-op

    return {{"request_id", requestId}, {"status", req->status}};
}

void AsyncRequestManager::WorkerLoop() {
    LOG_INFO(L"AsyncRequestManager worker thread started");

    while (running_) {
        std::shared_ptr<Request> req;

        {
            std::unique_lock<std::mutex> lock(mutex_);
            cv_.wait(lock, [this] { return !running_ || !workQueue_.empty(); });

            if (!running_) break;
            if (workQueue_.empty()) continue;

            req = workQueue_.front();
            workQueue_.pop();

            if (req->status == "cancelled") continue;
            req->status = "processing";
        }

        // Execute work outside lock
        try {
            json result = req->work();

            std::lock_guard<std::mutex> lock(mutex_);
            if (req->cancelFlag) {
                req->status = "cancelled";
            } else {
                req->status = result.value("success", false) ? "complete" : "error";
                req->result = result;
            }
        } catch (const std::exception& e) {
            std::lock_guard<std::mutex> lock(mutex_);
            req->status = "error";
            req->result = {{"success", false}, {"error", e.what()}};
        }

        req->completedAt = std::chrono::steady_clock::now();
    }

    LOG_INFO(L"AsyncRequestManager worker thread stopped");
}

void AsyncRequestManager::CleanupStale() {
    // Called under lock. Remove completed/error/cancelled entries older than 5 minutes.
    auto now = std::chrono::steady_clock::now();
    auto cutoff = std::chrono::minutes(5);

    for (auto it = requests_.begin(); it != requests_.end(); ) {
        auto& req = it->second;
        bool isFinished = (req->status == "complete" || req->status == "error" || req->status == "cancelled");
        if (isFinished && (now - req->completedAt) > cutoff) {
            it = requests_.erase(it);
        } else {
            ++it;
        }
    }
}
