#include <iostream>
#include <memory>
#include <openacc.h>


int main()
{
    size_t size_arr{1000};
    std::unique_ptr<int[]> arr{new int[size_arr]};
    std::unique_ptr<int[]> arr_new{new int[size_arr]};

    arr[0] = 1;
    arr_new[0] = 2;

    int *arr_cp = arr.get();
    int *arr_new_cp = arr_new.get(); 

    std::cout << arr_cp << '\n';
    std::cout << arr_new_cp << '\n' << '\n';

    #pragma acc data copyin(arr_cp[0:size_arr]) copyin(arr_new_cp[0:size_arr])
    {
        // возьмет указатели из объявления выше
        #pragma acc parallel
        {   
            printf("arr_cp[0] = %d\n", arr_cp[0]);
            printf("arr_new_cp[0] = %d\n", arr_new_cp[0]);
        }

        int* temp = arr_cp;
        arr_cp = arr_new_cp;
        arr_new_cp = temp;
        
        // свяжет имя с соответствующим указателем на GPU
        #pragma acc parallel present(arr_cp, arr_new_cp)
        {
            printf("arr_cp[0] = %d\n", arr_cp[0]);
            printf("arr_new_cp[0] = %d\n", arr_new_cp[0]);
        }
    }
    return 0;
}