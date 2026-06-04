#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <cmath>
#include <iomanip>
#include <vector>

// Относительный + абсолютный допуск для сравнения чисел с плавающей точкой
static const double REL_EPS = 1e-6;
static const double ABS_EPS = 1e-9;

bool nearly_equal(double a, double b) {
    double diff = std::abs(a - b);
    double ref  = std::max(std::abs(a), std::abs(b));
    return diff <= ABS_EPS || diff <= REL_EPS * ref;
}

// ─── Проверка файла с синусами ──────────────────────────────────────────────

bool test_sin(const std::string& filename) {
    std::ifstream in(filename);
    if (!in) {
        std::cerr << "[FAIL] Cannot open " << filename << "\n";
        return false;
    }

    std::string line;
    int total = 0, passed = 0, failed = 0;

    while (std::getline(in, line)) {
        if (line.empty() || line[0] == '#') continue;
        std::istringstream ss(line);
        int idx; double arg, result;
        ss >> idx >> arg >> result;

        double expected = std::sin(arg);
        ++total;
        if (nearly_equal(result, expected)) {
            ++passed;
        } else {
            ++failed;
            std::cerr << "  [MISMATCH] idx=" << idx
                      << " arg=" << arg
                      << " result=" << result
                      << " expected=" << expected << "\n";
        }
    }
    std::cout << "[sin]  total=" << total
              << " passed=" << passed
              << " failed=" << failed << "\n";
    return failed == 0;
}

// ─── Проверка файла с корнями ───────────────────────────────────────────────

bool test_sqrt(const std::string& filename) {
    std::ifstream in(filename);
    if (!in) {
        std::cerr << "[FAIL] Cannot open " << filename << "\n";
        return false;
    }

    std::string line;
    int total = 0, passed = 0, failed = 0;

    while (std::getline(in, line)) {
        if (line.empty() || line[0] == '#') continue;
        std::istringstream ss(line);
        int idx; double arg, result;
        ss >> idx >> arg >> result;

        double expected = std::sqrt(arg);
        ++total;
        if (nearly_equal(result, expected)) {
            ++passed;
        } else {
            ++failed;
            std::cerr << "  [MISMATCH] idx=" << idx
                      << " arg=" << arg
                      << " result=" << result
                      << " expected=" << expected << "\n";
        }
    }
    std::cout << "[sqrt] total=" << total
              << " passed=" << passed
              << " failed=" << failed << "\n";
    return failed == 0;
}

// ─── Проверка файла с pow ───────────────────────────────────────────────────

bool test_pow(const std::string& filename) {
    std::ifstream in(filename);
    if (!in) {
        std::cerr << "[FAIL] Cannot open " << filename << "\n";
        return false;
    }

    std::string line;
    int total = 0, passed = 0, failed = 0;

    while (std::getline(in, line)) {
        if (line.empty() || line[0] == '#') continue;
        std::istringstream ss(line);
        int idx; double base, exp, result;
        ss >> idx >> base >> exp >> result;

        double expected = std::pow(base, exp);
        ++total;
        if (nearly_equal(result, expected)) {
            ++passed;
        } else {
            ++failed;
            std::cerr << "  [MISMATCH] idx=" << idx
                      << " base=" << base
                      << " exp=" << exp
                      << " result=" << result
                      << " expected=" << expected << "\n";
        }
    }
    std::cout << "[pow]  total=" << total
              << " passed=" << passed
              << " failed=" << failed << "\n";
    return failed == 0;
}

// ─── main ──────────────────────────────────────────────────────────────────

int main() {
    std::cout << std::fixed << std::setprecision(10);
    std::cout << "=== Running tests ===\n";

    bool ok = true;
    ok &= test_sin ("results_sin.txt");
    ok &= test_sqrt("results_sqrt.txt");
    ok &= test_pow ("results_pow.txt");

    std::cout << "=====================\n";
    if (ok)
        std::cout << "All tests PASSED.\n";
    else
        std::cout << "Some tests FAILED.\n";

    return ok ? 0 : 1;
}