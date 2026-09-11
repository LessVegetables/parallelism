#include <iostream>
#include <cmath>
#include <chrono>
#include <iomanip>
#include <memory>
#include <openacc.h>

//export PGI_ACC_TIME=1

size_t array_size{1000000000};

int main(int argc, char const *argv[])
{
    double pi = 3.1415926535;
    double sum = 0;
    std::unique_ptr<double[]> array{new double[array_size]};
    double *array_point = array.get();
    

    auto start_time = std::chrono::high_resolution_clock::now();

    #pragma acc data create(array_point[0:array_size]) copy(sum) copyin(pi, array_size)
    {
        #pragma acc parallel loop
        for(int i = 0; i < array_size; i++){
            array_point[i] = sin(2 * pi*i/array_size);
        }

        #pragma acc parallel loop reduction(+:sum)
        for(int i = 0; i < array_size; i++){
            sum += array_point[i];
        }    
    }


    auto elapsed = std::chrono::high_resolution_clock::now() - start_time;
    auto time_microsec = std::chrono::duration_cast<std::chrono::microseconds>(elapsed).count();
    double time_sec = static_cast<double>(time_microsec) / 1000000;

    std::cout << std::fixed << std::setprecision(4);
    std::cout << "Duratioan programm: " << time_sec<< " seconds" << std::endl;

    std::cout << std::fixed << std::setprecision(20);
    std::cout << "sum = " << sum << std::endl;

    return 0;
}
