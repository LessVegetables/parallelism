#pragma once

#include <queue>
#include <unordered_map>
#include <functional>
#include <future>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <atomic>
#include <stdexcept>

// T — тип возвращаемого результата задач
template <typename T>
class Server {
public:
    Server() : next_id_(1), running_(false) {}

    ~Server() {
        if (running_) stop();
    }

    void start() {
        running_ = true;
        worker_ = std::jthread([this](std::stop_token stoken) {
            run(stoken);
        });
    }

    // дожидается завершения всех задач в очереди
    void stop() {
        worker_.request_stop();
        cond_var_.notify_all();
        if (worker_.joinable())
            worker_.join();
        running_ = false;
    }

    size_t add_task(std::function<T()> task) {
        std::packaged_task<T()> pt(std::move(task));
        size_t id;
        {
            std::lock_guard<std::mutex> lock(queue_mut_);
            id = next_id_++;
            futures_[id] = pt.get_future();
            task_queue_.push({id, std::move(pt)});
        }
        cond_var_.notify_one();
        return id;
    }

    T request_result(size_t id) {
        std::future<T> fut;
        {
            std::unique_lock<std::mutex> lock(res_mut_);
            // ждем пока результат появится в results_ или future станет доступен
            res_cv_.wait(lock, [this, id] {
                return results_.count(id) > 0;
            });
            T val = results_.at(id);
            results_.erase(id);
            return val;
        }
    }

private:
    struct TaskEntry {
        size_t id;
        std::packaged_task<T()> task;
    };

    void run(std::stop_token stoken) {
        while (true) {
            TaskEntry entry;
            {
                std::unique_lock<std::mutex> lock(queue_mut_);
                cond_var_.wait(lock, [this, &stoken] {                  //////////////?
                    return !task_queue_.empty() || stoken.stop_requested();
                });

                if (task_queue_.empty() && stoken.stop_requested())
                    break;

                if (task_queue_.empty()) continue;

                entry.id = task_queue_.front().id;
                entry.task = std::move(task_queue_.front().task);
                task_queue_.pop();
            }

            entry.task(); // выполняем задачу

            // получаем результат из future и сохраняем в results
            T result = futures_.at(entry.id).get();
            {
                std::lock_guard<std::mutex> lock(res_mut_);
                results_[entry.id] = result;
                futures_.erase(entry.id);
            }
            res_cv_.notify_all();
        }
    }

    std::queue<TaskEntry>              task_queue_;
    std::unordered_map<size_t, std::future<T>> futures_;
    std::unordered_map<size_t, T>      results_;

    std::mutex              queue_mut_;
    std::mutex              res_mut_;
    std::condition_variable cond_var_;
    std::condition_variable res_cv_;

    std::atomic<size_t>     next_id_;
    std::atomic<bool>       running_;
    std::jthread            worker_;
};
