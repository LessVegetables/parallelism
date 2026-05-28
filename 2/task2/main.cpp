
#include <iostream>
#include <fstream>
#include <iomanip>
#include <cstdlib>
#include <cstdint>
#include <cmath>
#include <chrono>
#include <omp.h>

const double PI = 3.14159265358979323846;
/* [a, b] */
const double a = -4.0;
const double b = 4.0;
/* n */
int nsteps = 40'000'000;

double func (double x)
{
    return exp(-x * x);
}

double integrate(double a, double b, int n)
{
    double h = (b - a) / n;
    double sum = 0.0;
    for (int i = 0; i < n; i++)
        sum += func(a + h * (i + 0.5));

    sum *= h;
    return sum;
}

double integrate_omp(double (*func)(double), double a, double b, int n)
{
    double h = (b - a) / n;    
    double sum = 0.0;
    
    #pragma omp parallel
    {        
        int nthreads = omp_get_num_threads();
        int threadid = omp_get_thread_num();
        int items_per_thread = n / nthreads;
        int lb = threadid * items_per_thread;
        int ub = (threadid == nthreads - 1) ? (n - 1) : (lb + items_per_thread - 1);

        double sumloc = 0.0;
        for (int i = lb; i <= ub; i++)
            sumloc += func(a + h * (i + 0.5));

        #pragma omp atomic
        sum += sumloc;
    }
    sum *= h;
    return sum;
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



double run_serial()
{
    const auto start{std::chrono::steady_clock::now()};

    double res = integrate(a, b, nsteps);

    const auto end{std::chrono::steady_clock::now()};
    const std::chrono::duration<double> elapsed_seconds{end - start};
    std::cout << std::fixed << std::setprecision(12)
        << "Result (serial):   " << res
        << "; error " << fabs(res - sqrt(PI)) << "\n";

    return elapsed_seconds.count();
}

double run_parallel(int threads)
{
    const auto start{std::chrono::steady_clock::now()};

    double res = integrate_omp(func, a, b, nsteps);

    const auto end{std::chrono::steady_clock::now()};
    const std::chrono::duration<double> elapsed_seconds{end - start};

    std::cout << std::fixed << std::setprecision(12)
        << "Result (parallel, " << threads << " threads): " << res
        << "; error " << fabs(res - sqrt(PI)) << "\n";

    return elapsed_seconds.count();;
}

int main(int argc, char **argv)
{
    // Sizes to benchmark
    int sizes[2] = {40'000'000, 80'000'000}; // nsteps
    int thread_counts[] = {1, 2, 3, 4, 5, 6, 7, 8, 16, 20, 40};
    int num_sizes = 2;
    int num_threads = sizeof(thread_counts) / sizeof(thread_counts[0]);

    // Open CSV for writing
    std::ofstream csv("results.csv");
    csv << "size,threads,time,speedup\n";

    for (int s = 0; s < num_sizes; s++) {
        nsteps = sizes[s];

        std::cout << "\n=== Size " << nsteps << " ===" << std::endl;

        // Baseline: serial time
        std::cout << "Running serial..." << std::flush;
        double t1 = run_serial();
        std::cout << " " << t1 << " sec" << std::endl;
        csv << nsteps << "," << 1 << "," << t1 << "," << 1.0 << "\n";

        // Parallel runs
        for (int k = 1; k < num_threads; k++) {
            int p = thread_counts[k];
            std::cout << "Running p=" << p << "..." << std::flush;
            double tp = run_parallel(p);
            double sp = t1 / tp;
            std::cout << " " << tp << " sec  (S=" << sp << ")" << std::endl;
            csv << nsteps << "," << p << "," << tp << "," << sp << "\n";
        }
    }

    csv.close();
    std::cout << "\nResults saved to results.csv" << std::endl;
    std::cout << "Now run: python3 plot_table.py" << std::endl;
    return 0;
}