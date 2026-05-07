#include <stdio.h>
#include <omp.h>
#include <time.h>
#include <stdlib.h>
#include <inttypes.h>

// using namespace std;

/* matrix_vector_product_omp: Compute matrix-vector product c[m] = a[m][n] * b[n] */
void matrix_vector_product_omp(double *a, double *b, double *c, int m, int n)
{
    #pragma omp parallel
    {
        int nthreads = omp_get_num_threads();
        int threadid = omp_get_thread_num();
        int items_per_thread = m / nthreads;
        int lb = threadid * items_per_thread;
        int ub = (threadid == nthreads - 1) ? (m - 1) : (lb + items_per_thread - 1);
        for (int i = lb; i <= ub; i++) {
            c[i] = 0.0;
            for (int j = 0; j < n; j++)
            c[i] += a[i * n + j] * b[j];
        }
    }
}


void run_parallel(int m, int n)
{
    double *a, *b, *c;
    // Allocate memory for 2-d array a[m, n]
    a = malloc(sizeof(*a) * m * n);
    b = malloc(sizeof(*b) * n);
    c = malloc(sizeof(*c) * m);
    for (int i = 0; i < m; i++) {
        for (int j = 0; j < n; j++)
        a[i * n + j] = i + j;
    }

    for (int j = 0; j < n; j++)
        b[j] = j;

    double t = time();
    matrix_vector_product_omp(a, b, c, m, n);
    t = time() - t;

    printf("Elapsed time (parallel): %.6f sec.\n", t);
    free(a);
    free(b);
    free(c);
}

int main(int argc, char **argv)
{
    int m = 10, n = 10;
    printf("Matrix-vector product (c[m] = a[m, n] * b[n]; m = %d, n = %d)\n", m, n);
    printf("Memory used: %" PRIu64 " MiB\n", ((m * n + m + n) * sizeof(double)) >> 20);
    // run_serial();
    run_parallel(m, n);
    return 0;
}