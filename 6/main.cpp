#include <iostream>
#include <fstream>
#include <iomanip>
#include <cmath>
#include <chrono>
#include <string>
#include <boost/program_options.hpp>

#ifdef USE_NVTX
#include <nvtx3/nvToolsExt.h>
#define NVTX_PUSH(n) nvtxRangePushA(n)
#define NVTX_POP()   nvtxRangePop()
#else
#define NVTX_PUSH(n)
#define NVTX_POP()
#endif

namespace po = boost::program_options;

// Corner values (clockwise from top-left): 10, 20, 30, 20
static const double CORNER_TL = 10.0;
static const double CORNER_TR = 20.0;
static const double CORNER_BR = 30.0;
static const double CORNER_BL = 20.0;

// Fill boundary edges with linear interpolation between corners.
// Interior is set to 0. Both A and Anew get the same boundary.
static void initialize(double* A, double* Anew, int n) {
    const int total = n * n;
    for (int k = 0; k < total; k++) {
        A[k] = 0.0;
        Anew[k] = 0.0;
    }

    const double inv = 1.0 / (n - 1);

    // Top row (i=0): TL -> TR
    // Bottom row (i=n-1): BL -> BR
    for (int j = 0; j < n; j++) {
        double t = j * inv;
        double top = CORNER_TL + (CORNER_TR - CORNER_TL) * t;
        double bot = CORNER_BL + (CORNER_BR - CORNER_BL) * t;
        A[j]             = Anew[j]             = top;
        A[(n-1)*n + j]   = Anew[(n-1)*n + j]   = bot;
    }

    // Left col (j=0): TL -> BL
    // Right col (j=n-1): TR -> BR
    for (int i = 0; i < n; i++) {
        double t = i * inv;
        double left  = CORNER_TL + (CORNER_BL - CORNER_TL) * t;
        double right = CORNER_TR + (CORNER_BR - CORNER_TR) * t;
        A[i*n]         = Anew[i*n]         = left;
        A[i*n + (n-1)] = Anew[i*n + (n-1)] = right;
    }
}

// One Jacobi iteration: 5-point stencil over interior nodes.
// When compute_error is true, also reduces the inf-norm error and returns it;
// otherwise it skips the reduction (cheaper) and returns 0.
static double calcNext(const double* __restrict__ A,
                             double* __restrict__ Anew, int n,
                             bool compute_error) {
    double error = 0.0;
    if (compute_error) {
        #pragma acc parallel loop collapse(2) reduction(max:error) \
            present(A[0:n*n], Anew[0:n*n])
        for (int i = 1; i < n-1; i++) {
            for (int j = 1; j < n-1; j++) {
                Anew[i*n + j] = 0.25 * (A[(i-1)*n + j] + A[(i+1)*n + j] +
                                         A[i*n + j-1]   + A[i*n + j+1]);
                error = fmax(error, fabs(Anew[i*n + j] - A[i*n + j]));
            }
        }
    } else {
        #pragma acc parallel loop collapse(2) present(A[0:n*n], Anew[0:n*n])
        for (int i = 1; i < n-1; i++) {
            for (int j = 1; j < n-1; j++) {
                Anew[i*n + j] = 0.25 * (A[(i-1)*n + j] + A[(i+1)*n + j] +
                                         A[i*n + j-1]   + A[i*n + j+1]);
            }
        }
    }
    return error;
}

// Copy new values into A (boundary rows/cols stay untouched).
static void swapBuffers(double* __restrict__ A,
                        const double* __restrict__ Anew, int n) {
    #pragma acc parallel loop collapse(2) present(A[0:n*n], Anew[0:n*n])
    for (int i = 1; i < n-1; i++) {
        for (int j = 1; j < n-1; j++) {
            A[i*n + j] = Anew[i*n + j];
        }
    }
}

static void saveMatrix(const double* A, int n, const std::string& path) {
    std::ofstream f(path);
    f << std::fixed << std::setprecision(6);
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            if (j) f << ' ';
            f << A[i*n + j];
        }
        f << '\n';
    }
}

static void printMatrix(const double* A, int n) {
    std::cout << std::fixed << std::setprecision(4);
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            std::cout << std::setw(9) << A[i*n + j];
        }
        std::cout << '\n';
    }
}

int main(int argc, char** argv) {
    int    n        = 256;
    double tol      = 1e-6;
    int    iter_max = 1000000;
    int    check    = 1;

    po::options_description desc("Heat equation solver (5-point Jacobi + OpenACC)");
    desc.add_options()
        ("help,h",       "Show this help")
        ("size,n",       po::value<int>   (&n)       ->default_value(256),     "Grid side length (NxN)")
        ("tolerance,t",  po::value<double>(&tol)     ->default_value(1e-6),    "Convergence tolerance")
        ("iterations,i", po::value<int>   (&iter_max)->default_value(1000000), "Max iterations")
        ("check,c",      po::value<int>   (&check)   ->default_value(1),       "Compute error every C iterations");

    po::variables_map vm;
    try {
        po::store(po::parse_command_line(argc, argv, desc), vm);
        po::notify(vm);
    } catch (const po::error& e) {
        std::cerr << "Error: " << e.what() << '\n' << desc << '\n';
        return 1;
    }
    if (vm.count("help")) { std::cout << desc << '\n'; return 0; }
    if (check < 1) check = 1;

    std::cout << "Grid: " << n << "x" << n
              << "  tol: " << tol
              << "  max_iter: " << iter_max
              << "  check: " << check << '\n';

    double* A    = new double[n * n];
    double* Anew = new double[n * n];

    initialize(A, Anew, n);

    double error = 1.0;
    int    iter  = 0;

    auto t0 = std::chrono::steady_clock::now();

    #pragma acc data copyin(A[0:n*n], Anew[0:n*n])
    {
        NVTX_PUSH("solve");
        while (error > tol && iter < iter_max) {
            bool compute_error = (iter % check == 0);

            NVTX_PUSH("calcNext");
            double e = calcNext(A, Anew, n, compute_error);
            NVTX_POP();

            if (compute_error) error = e;

            NVTX_PUSH("swap");
            swapBuffers(A, Anew, n);
            NVTX_POP();

            iter++;
        }
        NVTX_POP();

        #pragma acc update host(A[0:n*n])
    }

    auto t1 = std::chrono::steady_clock::now();
    double elapsed = std::chrono::duration<double>(t1 - t0).count();

    std::cout << "Iterations: " << iter << '\n';
    std::cout << "Error:      " << std::scientific << std::setprecision(6) << error << '\n';
    std::cout << "Time:       " << std::fixed << std::setprecision(3) << elapsed << " s\n";

    // Save result to file for verification
    std::string fname = "result_" + std::to_string(n) + ".txt";
    saveMatrix(A, n, fname);
    std::cout << "Saved:      " << fname << '\n';

    // Print grid for small sizes (required for 10x10 and 13x13)
    if (n <= 13) {
        std::cout << "\nGrid values (" << n << "x" << n << "):\n";
        printMatrix(A, n);
    }

    delete[] A;
    delete[] Anew;
    return 0;
}
