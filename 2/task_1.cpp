#include <iostream>
#include <cstdlib>
#include <cstdint>
#include <omp.h>

// Matrix dimensions (set via command line or defaults)
static int M = 20000;
static int N = 20000;

static double wtime()
{
    return omp_get_wtime();
}

#include <chrono>
/*
    Для C++ используйте библиотеку chrono
*/
void timeChrono()
{
    const auto start{std::chrono::steady_clock::now()};
    // sleep(1);
    const auto end{std::chrono::steady_clock::now()};
    const std::chrono::duration<double> elapsed_seconds{end - start};

    std::cout << "Your calculations took " <<
                elapsed_seconds.count() <<
                " seconds to run chrono.\n"; // Before C++20
    // std::cout << elapsed_seconds << '\n'; // C++20's chrono::duration operator<<
}

/*
 * matrix_vector_product: последовательное умножение матрицы на вектор
 * c[m] = a[m][n] * b[n]
 */
void matrix_vector_product(const double *a, const double *b, double *c, int m, int n)
{
    for (int i = 0; i < m; i++) {
        c[i] = 0.0;
        for (int j = 0; j < n; j++)
            c[i] += a[(long long)i * n + j] * b[j];
    }
}


/* matrix_vector_product_omp: Compute matrix-vector product c[m] = a[m][n] * b[n] */
void matrix_vector_product_omp(const double *a, const double *b, double *c, int m, int n){
    #pragma omp parallel
    {
        int nthreads = omp_get_num_threads();
        int threadid = omp_get_thread_num();
        int items_per_thread = m / nthreads;
        int lb = threadid * items_per_thread;
        int ub = (threadid == nthreads - 1) ? (m - 1) : (lb + items_per_thread - 1);
        for (int i = lb; i <= ub; i++)
        {
            c[i] = 0.0;
            for (int j = 0; j < n; j++)
                c[i] += a[(long long)i * n + j] * b[j];
        }
    }
}


double run_serial()
{
    long long size = (long long)M * N;
    double *a = new double[size];
    double *b = new double[N];
    double *c = new double[M];

    // Инициализация (последовательная)
    for (int i = 0; i < M; i++)
        for (int j = 0; j < N; j++)
            a[(long long)i * N + j] = (double)(i + j);
    for (int j = 0; j < N; j++)
        b[j] = (double)j;

    // double t = wtime();
    const auto start{std::chrono::steady_clock::now()};
    matrix_vector_product(a, b, c, M, N);
    // t = wtime() - t;
    const auto end{std::chrono::steady_clock::now()};

    const std::chrono::duration<double> elapsed_seconds{end - start};

    double t = elapsed_seconds.count();
    std::cout << "Elapsed time (serial): " << t << " sec." << std::endl;

    delete[] a;
    delete[] b;
    delete[] c;
    return t;
}


double run_parallel(int nthreads)
{
    long long size = (long long)M * N;
    double *a = new double[size];
    double *b = new double[N];
    double *c = new double[M];

    // ---- Параллельная инициализация (first-touch) ----
    #pragma omp parallel num_threads(nthreads)
    {
        int nt = omp_get_num_threads();
        int tid = omp_get_thread_num();
        int items = M / nt;
        int lb = tid * items;
        int ub = (tid == nt - 1) ? (M - 1) : (lb + items - 1);

        for (int i = lb; i <= ub; i++) {
            for (int j = 0; j < N; j++)
                a[(long long)i * N + j] = (double)(i + j);
            c[i] = 0.0;
        }
    }
    // b инициализируется последовательно (мал по размеру)
    for (int j = 0; j < N; j++)
        b[j] = (double)j;

    // ---- Параллельное вычисление ----
    // double t = wtime();
    const auto start{std::chrono::steady_clock::now()};
    matrix_vector_product_omp(a, b, c, M, N);
    // t = wtime() - t;
    const auto end{std::chrono::steady_clock::now()};
    const std::chrono::duration<double> elapsed_seconds{end - start};
    double t = elapsed_seconds.count();

    std::cout << "  Threads: " << nthreads
              << "  Time: " << t << " sec." << std::endl;

    delete[] a;
    delete[] b;
    delete[] c;
    return t;
}


int main(int argc, char **argv)
{
    if (argc >= 3) {
        M = std::atoi(argv[1]);
        N = std::atoi(argv[2]);
    }

    long long mem_mib = ((long long)M * N + M + N) * sizeof(double) / (1024 * 1024);
    std::cout << "========================================" << std::endl;
    std::cout << "Matrix-vector product  c[m] = a[m,n] * b[n]" << std::endl;
    std::cout << "M = " << M << ", N = " << N << std::endl;
    std::cout << "Memory: ~" << mem_mib << " MiB" << std::endl;
    std::cout << "========================================" << std::endl;

    // Последовательная версия — для справки
    run_serial();
    std::cout << "(serial shown for reference; speedup is computed as T1/Tp)\n" << std::endl;

    // Параллельные запуски
    int thread_counts[] = {1, 2, 4, 7, 8, 16, 20, 40};
    int num_cases = sizeof(thread_counts) / sizeof(thread_counts[0]);

    // T1 — параллельная программа на 1 потоке (честная база для Sp)
    std::cout << "--- Scalability analysis (Sp = T / Tp) ---" << std::endl;
    double t1 = run_serial();
    std::cout << "  T (baseline) = " << t1 << " sec." << std::endl;

    std::cout << "\nThreads\tTime(s)\tSpeedup" << std::endl;
    // p=1 уже известен
    std::cout << "  1\t" << t1 << "\t1.0" << std::endl;

    for (int k = 1; k < num_cases; k++) {   // начинаем с k=1, p=2
        int p = thread_counts[k];
        double t_par = run_parallel(p);
        double speedup = t1 / t_par;
        std::cout << "  " << p << "\t" << t_par << "\t" << speedup << std::endl;
    }

    return 0;
}