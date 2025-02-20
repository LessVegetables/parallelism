#include <iostream>
#include <vector>
#include <math.h>

using namespace std;

#ifndef TYPE
#define TYPE double
#endif


int main()
{
    std::cout << "TYPE set to: " << typeid(TYPE).name() << std::endl;

    vector<TYPE> arr;

    #define MY_PI 3.1415926536
    
    // 0.000000628318531
    TYPE step = (2.0 * MY_PI) / 10000000.0;
    TYPE alpha = 0.0;

    for (int i = 0; i < 10000000; i++)
    {
        arr.push_back(sin(alpha));
        alpha = i * step;
        // alpha = i * 2.0 * MY_PI / 10000000.0; // alpha += step;
    }
    // cout << "2pi: " << alpha << "\npi: " << alpha / 2.0 << endl;

    TYPE sum = 0.0;
    for (int i = 0; i < 10000000; i++)
    {
        sum += arr[i];
    }
    // cout << arr.size() << endl;
    cout << sum << endl;
    return 0;
}

// g++ daniel-1.cpp -o daniel