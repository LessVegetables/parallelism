#include <time.h>
#include <stdio.h>
#include <unistd.h>
#include <chrono>
#include <iostream>

// Затраченное время процессором, использовать только внутри одного процесса
// https://en.cppreference.com/w/c/chrono/clock
void timeClock()
{
    clock_t start = clock();
    sleep(1);
    clock_t end = clock();
    float seconds = (float)(end - start) / CLOCKS_PER_SEC;
    printf("Your calculations took %.2lf seconds to run clock.\n", seconds);
}

// Настенные часы, точность секунды
void timeTime_t()
{
    time_t start, end;
    double dif;

    time(&start);
    sleep(1);
    time(&end);
    dif = difftime(end, start);
    printf("Your calculations took %.2lf seconds to run time_t.\n", dif);
}

// рекомендуеться при написании на C
double cpuSecond()
{
    struct timespec ts;
    timespec_get(&ts, TIME_UTC);
    return ((double)ts.tv_sec + (double)ts.tv_nsec * 1.e-9);
}

/*
    Для C++ используйте библиотеку chrono
*/
void timeChrono()
{
    const auto start{std::chrono::steady_clock::now()};
    sleep(1);
    const auto end{std::chrono::steady_clock::now()};
    const std::chrono::duration<double> elapsed_seconds{end - start};

    std::cout << "Your calculations took " <<
                elapsed_seconds.count() <<
                " seconds to run chrono.\n"; // Before C++20
    // std::cout << elapsed_seconds << '\n'; // C++20's chrono::duration operator<<
}

void timeMillis()
{
    double start = cpuSecond();
    sleep(1);
    double stop = cpuSecond();
    double dif = stop - start;
    printf("Your calculations took %.2lf seconds to run millis.\n", dif);
}

int main()
{
    timeClock();
    timeTime_t();
    timeMillis();
    timeChrono();
    return 0;
}