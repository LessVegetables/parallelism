#include <iostream>
#include <vector>
#include <math.h>
#include <iomanip>
#include <limits>

#ifndef TYPE
#define TYPE double
#endif

int main()
{
    std::cout << "Type set to: " << typeid(TYPE).name() << std::endl;

    std::vector<TYPE> arr;

    TYPE param = 45.0;

    for (int i = 0; i < 10000000; i++)
    {
        arr.push_back(param);
    }

    TYPE sum = 0.0;

    for (int i = 0; i < 10000000; i++)
    {
        sum += arr[i];
    }

    std::cout << std::fixed
              << std::setprecision(std::numeric_limits<double>::max_digits10)
              << std::endl;

    std::cout
        << "sum(arr) = " << sum << std::endl;

    return 0;
}