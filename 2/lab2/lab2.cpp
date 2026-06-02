#include <iostream>
#include <fstream>
#include <iomanip>
#include <cstdlib>
#include <cmath>
#include <chrono>
#include <omp.h>

const double eps = 1e-6;    // желаемая точность

// -------------------------------------------------------
// Helper: allocate N×N matrix and N-vectors, fill with a
// diagonally dominant system that has a known solution.
//
// We use A[i][i] = N+1,
//        A[i][j] = 1 (i≠j),
//        X_true[i] = i+1
// so F[i] = sum_j A[i][j] * X_true[j].
// -------------------------------------------------------
void build_system(int N, double** A, double* F, double* X_true)
{
    for (int i = 0; i < N; i++) {
        X_true[i] = i + 1.0;
        for (int j = 0; j < N; j++)
            A[i][j] = (i == j) ? (N + 1.0) : 1.0;
    }
    for (int i = 0; i < N; i++) {
        F[i] = 0.0;
        for (int j = 0; j < N; j++)
            F[i] += A[i][j] * X_true[j];
    }
}

/// N - размерность матрицы; A[N][N] - матрица коэффициентов, F[N] - столбец свободных членов,
/// X[N] - начальное приближение, ответ записывается также в X[N];
void Jacobi_serial (int N, double** A, double* F, double* X)
{
	double* TempX = new double[N];
	double norm; // норма, определяемая как наибольшая разность компонент столбца иксов соседних итераций.

	do {
		for (int i = 0; i < N; i++) {
			TempX[i] = F[i];
			for (int g = 0; g < N; g++) {
				if (i != g)
					TempX[i] -= A[i][g] * X[g];
			}
			TempX[i] /= A[i][i];
		}
        norm = fabs(X[0] - TempX[0]);
		for (int h = 0; h < N; h++) {
			if (fabs(X[h] - TempX[h]) > norm)
				norm = fabs(X[h] - TempX[h]);
			X[h] = TempX[h];
		}
	} while (norm > eps);
	delete[] TempX;
}

// -------------------------------------------------------
// Variant 1: separate #pragma omp parallel for per loop
// -------------------------------------------------------
void Jacobi_v1(int N, double** A, double* F, double* X, int threads)
{
    double* TempX = new double[N];
    double norm;
    do {
        #pragma omp parallel for num_threads(threads) schedule(static)
        for (int i = 0; i < N; i++) {
            TempX[i] = F[i];
            for (int g = 0; g < N; g++)
                if (i != g) TempX[i] -= A[i][g] * X[g];
            TempX[i] /= A[i][i];
        }

        norm = fabs(X[0] - TempX[0]);

        #pragma omp parallel for num_threads(threads) schedule(static) reduction(max: norm)
        for (int h = 0; h < N; h++) {
            if (fabs(X[h] - TempX[h]) > norm)
                norm = fabs(X[h] - TempX[h]);
        }

        for (int h = 0; h < N; h++)
            X[h] = TempX[h];

    } while (norm > eps);
    delete[] TempX;
}

// -------------------------------------------------------
// Variant 2: single #pragma omp parallel enclosing the full loop body
// -------------------------------------------------------
void Jacobi_v2(int N, double** A, double* F, double* X, int threads)
{
    double* TempX = new double[N];
    double norm;

    #pragma omp parallel num_threads(threads) default(shared)
    {
        do {
            #pragma omp for schedule(static)
            for (int i = 0; i < N; i++) {
                TempX[i] = F[i];
                for (int g = 0; g < N; g++)
                    if (i != g) TempX[i] -= A[i][g] * X[g];
                TempX[i] /= A[i][i];
            }
            // implicit barrier after omp for — all TempX[i] are ready

            #pragma omp single
            norm = 0.0;
            // implicit barrier after single

            #pragma omp for schedule(static) reduction(max: norm)
            for (int h = 0; h < N; h++) {
                double diff = fabs(X[h] - TempX[h]);
                if (diff > norm) norm = diff;
            }
            // implicit barrier — norm is final

            #pragma omp single
            for (int h = 0; h < N; h++)
                X[h] = TempX[h];

            // implicit barrier — X updated, all threads see new norm

        } while (norm > eps);
    }

    delete[] TempX;
}

// -------------------------------------------------------
// Runner helpers (mirror run_serial / run_parallel from lab 1)
// -------------------------------------------------------
double run_serial(int N, double** A, double* F, double* X, double* X_true)
{
    for (int i = 0; i < N; i++) X[i] = 0.0;

    const auto start{std::chrono::steady_clock::now()};
    Jacobi_serial(N, A, F, X);
    const auto end{std::chrono::steady_clock::now()};
    const std::chrono::duration<double> elapsed{end - start};

    double err = 0.0;
    for (int i = 0; i < N; i++)
        err = std::max(err, std::fabs(X[i] - X_true[i]));

    std::cout << std::fixed << std::setprecision(12)
              << "Result (serial):            max_err " << err << "\n";

    return elapsed.count();
}

double run_parallel_v1(int N, double** A, double* F, double* X, double* X_true, int threads)
{
    for (int i = 0; i < N; i++) X[i] = 0.0;

    const auto start{std::chrono::steady_clock::now()};
    Jacobi_v1(N, A, F, X, threads);
    const auto end{std::chrono::steady_clock::now()};
    const std::chrono::duration<double> elapsed{end - start};

    double err = 0.0;
    for (int i = 0; i < N; i++)
        err = std::max(err, std::fabs(X[i] - X_true[i]));

    std::cout << std::fixed << std::setprecision(12)
              << "Result (v1, " << std::setw(2) << threads << " threads): max_err " << err << "\n";

    return elapsed.count();
}

double run_parallel_v2(int N, double** A, double* F, double* X, double* X_true, int threads)
{
    for (int i = 0; i < N; i++) X[i] = 0.0;

    const auto start{std::chrono::steady_clock::now()};
    Jacobi_v2(N, A, F, X, threads);
    const auto end{std::chrono::steady_clock::now()};
    const std::chrono::duration<double> elapsed{end - start};

    double err = 0.0;
    for (int i = 0; i < N; i++)
        err = std::max(err, std::fabs(X[i] - X_true[i]));

    std::cout << std::fixed << std::setprecision(12)
              << "Result (v2, " << std::setw(2) << threads << " threads): max_err " << err << "\n";

    return elapsed.count();
}


int main()
{
    int sizes[] = {1000, 2500, 5000};   // adjust until serial takes ≥30s on your node
    int thread_counts[] = {1, 2, 3, 4, 5, 6, 7, 8, 16, 20, 40};
    int num_sizes   = sizeof(sizes)        / sizeof(sizes[0]);
    int num_threads = sizeof(thread_counts) / sizeof(thread_counts[0]);

    std::ofstream csv("results_jacobi.csv");
    csv << "size,variant,threads,time,speedup\n";

    for (int s = 0; s < num_sizes; s++) {
        int N = sizes[s];

        // Allocate once per size — same data for every thread count
        double** A    = new double*[N];
        for (int i = 0; i < N; i++) A[i] = new double[N];
        double* F      = new double[N];
        double* X      = new double[N];
        double* X_true = new double[N];
        build_system(N, A, F, X_true);

        std::cout << "\n=== N = " << N << " ===" << std::endl;

        // Baseline: serial
        std::cout << "Running serial..." << std::flush;
        double t1 = run_serial(N, A, F, X, X_true);
        std::cout << " " << t1 << " sec" << std::endl;
        csv << N << ",serial," << 1 << "," << t1 << "," << 1.0 << "\n";

        // Variant 1 and 2 across thread counts
        for (int k = 0; k < num_threads; k++) {
            int p = thread_counts[k];

            std::cout << "Running v1 p=" << p << "..." << std::flush;
            double tv1 = run_parallel_v1(N, A, F, X, X_true, p);
            double sv1 = t1 / tv1;
            std::cout << " " << tv1 << " sec  (S=" << sv1 << ")" << std::endl;
            csv << N << ",v1," << p << "," << tv1 << "," << sv1 << "\n";

            std::cout << "Running v2 p=" << p << "..." << std::flush;
            double tv2 = run_parallel_v2(N, A, F, X, X_true, p);
            double sv2 = t1 / tv2;
            std::cout << " " << tv2 << " sec  (S=" << sv2 << ")" << std::endl;
            csv << N << ",v2," << p << "," << tv2 << "," << sv2 << "\n";
        }

        for (int i = 0; i < N; i++) delete[] A[i];
        delete[] A; delete[] F; delete[] X; delete[] X_true;
    }

    csv.close();
    std::cout << "\nResults saved to results_jacobi.csv" << std::endl;
    return 0;
}