#include <iostream>
#include <openacc.h>


int main()
{
    //kernels or parallel
    #pragma acc parallel
    {   
        for(size_t i = 0; i < 3; ++i)
        {
            printf("Hello_ACC\n");
        }
       
        for(size_t i = 0; i < 3; ++i)
        {
            printf("Hello_ACC\n");
        }
    }
    return 0;
}
