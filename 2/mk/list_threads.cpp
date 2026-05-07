#include <cstdio>
#include <chrono>
#include <thread>

#include <omp.h>

int main(int argc, char **argv)
{
#pragma omp parallel num_threads(6)
    {
        printf("Hello, multithreaded world: thread %d of %d\n",
               omp_get_thread_num(), omp_get_num_threads());
        /* Sleep for 30 seconds */
        std::this_thread::sleep_for(std::chrono::seconds(30));
    }
    return 0;
}

// ps -eLo pid,tid,psr,args | grep list_threads