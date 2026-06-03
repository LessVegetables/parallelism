#include <iostream>
#include <fstream>
#include <thread>
#include <cmath>
#include <random>
#include <vector>
#include <string>
#include <iomanip>
#include <sstream>

#include "server.hpp"


template <typename T>
T fun_sin(T arg) { return std::sin(arg); }

template <typename T>
T fun_sqrt(T arg) { return std::sqrt(arg); }

template <typename T>
T fun_pow(T x, T y) { return std::pow(x, y); }


// Клиент 1: вычисление синуса
void client_sin(Server<double>& server, int N, const std::string& filename) {
    std::mt19937 rng(42);
    std::uniform_real_distribution<double> dist(-10.0, 10.0);

    // Собираем (аргумент, id)
    std::vector<std::pair<double, size_t>> tasks;
    tasks.reserve(N);

    for (int i = 0; i < N; ++i) {
        double arg = dist(rng);
        size_t id = server.add_task([arg]() -> double { return fun_sin(arg); });
        tasks.push_back({arg, id});
    }

    std::ofstream out(filename);
    out << std::fixed << std::setprecision(10);
    out << "# sin tasks: " << N << "\n";
    out << std::left
        << std::setw(6)  << "# idx"
        << std::setw(20) << "arg"
        << std::setw(20) << "result" << "\n";

    for (int i = 0; i < N; ++i) {
        double result = server.request_result(tasks[i].second);
        out << std::setw(6)  << (i + 1)
            << std::setw(20) << tasks[i].first
            << std::setw(20) << result << "\n";
    }
    std::cout << "[client_sin]  Done. Results saved to " << filename << "\n";
}

// Клиент 2: вычисление квадратного корня
void client_sqrt(Server<double>& server, int N, const std::string& filename) {
    std::mt19937 rng(123);
    std::uniform_real_distribution<double> dist(0.0, 1000.0);

    std::vector<std::pair<double, size_t>> tasks;
    tasks.reserve(N);

    for (int i = 0; i < N; ++i) {
        double arg = dist(rng);
        size_t id = server.add_task([arg]() -> double { return fun_sqrt(arg); });
        tasks.push_back({arg, id});
    }

    std::ofstream out(filename);
    out << std::fixed << std::setprecision(10);
    out << "# sqrt tasks: " << N << "\n";
    out << std::left
        << std::setw(6)  << "# idx"
        << std::setw(20) << "arg"
        << std::setw(20) << "result" << "\n";

    for (int i = 0; i < N; ++i) {
        double result = server.request_result(tasks[i].second);
        out << std::setw(6)  << (i + 1)
            << std::setw(20) << tasks[i].first
            << std::setw(20) << result << "\n";
    }
    std::cout << "[client_sqrt] Done. Results saved to " << filename << "\n";
}

// Клиент 3: возведение в степень
void client_pow(Server<double>& server, int N, const std::string& filename) {
    std::mt19937 rng(777);
    std::uniform_real_distribution<double> base_dist(1.0, 10.0);
    std::uniform_real_distribution<double> exp_dist(0.5, 5.0);

    struct PowArgs { double x, y; };
    std::vector<std::pair<PowArgs, size_t>> tasks;
    tasks.reserve(N);

    for (int i = 0; i < N; ++i) {
        PowArgs a{base_dist(rng), exp_dist(rng)};
        size_t id = server.add_task([a]() -> double { return fun_pow(a.x, a.y); });
        tasks.push_back({a, id});
    }

    std::ofstream out(filename);
    out << std::fixed << std::setprecision(10);
    out << "# pow tasks: " << N << "\n";
    out << std::left
        << std::setw(6)  << "# idx"
        << std::setw(20) << "base"
        << std::setw(20) << "exp"
        << std::setw(20) << "result" << "\n";

    for (int i = 0; i < N; ++i) {
        double result = server.request_result(tasks[i].second);
        out << std::setw(6)  << (i + 1)
            << std::setw(20) << tasks[i].first.x
            << std::setw(20) << tasks[i].first.y
            << std::setw(20) << result << "\n";
    }
    std::cout << "[client_pow]  Done. Results saved to " << filename << "\n";
}


int main() {
    const int N = 100;

    Server<double> server;
    server.start();
    std::cout << "Server started.\n";

    std::thread t1(client_sin,  std::ref(server), N, "results_sin.txt");
    std::thread t2(client_sqrt, std::ref(server), N, "results_sqrt.txt");
    std::thread t3(client_pow,  std::ref(server), N, "results_pow.txt");

    t1.join();
    t2.join();
    t3.join();

    server.stop();
    std::cout << "Server stopped.\n";
    return 0;
}
