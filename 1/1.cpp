#include <iostream>
#include <vector>
#include <iomanip>
#include <limits>

#define _USE_MATH_DEFINES
#include <cmath>

#ifndef TYPE
#define TYPE double
#endif

#ifndef ARR_LENGTH
#define ARR_LENGTH 10'000'000.0
#endif

int main()
{
    std::cout << "Type set to: " << typeid(TYPE).name() << std::endl;

    std::vector<TYPE> arr;
    TYPE delta = (2.0 * M_PI) / ARR_LENGTH;
    TYPE sum = 0.0;

    for (int i = 0; i < ARR_LENGTH; i++)
    {
        arr.push_back(sin(delta));
        sum += arr[i];
        sum /= (2.0 * M_PI);
    }

    std::cout << std::fixed
              << std::setprecision(std::numeric_limits<double>::max_digits10);

    std::cout << "sin(delta) = " << sin(delta) << std::endl;
    std::cout << "sum(arr)   = " << sum << std::endl;
    std::cout << std::endl;

    return 0;
}