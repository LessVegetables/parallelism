// #include <stdio.h>
#include <iostream>
#include <omp.h>

int main (int argc, char **argv){
    #pragma omp parallel    /* <-- Fork */
    {
        std::cout << "Hello, multithreaded world: thread " << omp_get_thread_num() << " of " << omp_get_num_threads() << std::endl;
    }   /* <-- Barrier & join */
    return 0;
}