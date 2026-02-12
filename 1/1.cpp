#include <iostream>
#include <vector>
#include <cmath>
#include <iomanip>
#include <limits>

#ifndef TYPE
#define TYPE double
#endif

int main()
{
    std::cout << "Type set to: " << typeid(TYPE).name() << std::endl;

    std::vector<TYPE> arr;

    TYPE param = 0.52359878;
    TYPE sum = 0.0;

    for (int i = 0; i < 10000000; i++)
    {
        arr.push_back(sin(param));
        sum += arr[i];
    }

    std::cout << std::fixed
              << std::setprecision(std::numeric_limits<double>::max_digits10)
              << std::endl;

    std::cout << "sum(arr) = " << sum << std::endl;

    return 0;
}