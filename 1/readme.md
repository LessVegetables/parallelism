# Task 1
###### *From 02/05*

Fill a float/double array with sine values ​​(one period for the entire array length), with the number of elements equal to 10^7. Calculate the sum and output it to the terminal.
Write CMake files for the build. It should be possible to select the array type (float or double) during the build.

# Compiling / running

If not already in this (`/parallels/1/`) directory:
```sh
cd 1
```

Compile with cmake/make:
```sh
mkdir build && cd build
cmake ..
make
```
CMake can generate either or both precision-specific binaries: main_d (uses a double array), main_f (uses a float array). By default, it builds both.
To build only one of the programs, set the `-DFLAG_TYPE` flag to either `d` for double or `f` for float.
```sh
cmake .. -DFLAG_TYPE=d
make
```
*or*
```sh
cmake .. -DFLAG_TYPE=f
make
```

# Run
Double variant:
```sh
./main_d
```

Float variant:
```sh
./main_f
```

# Result

With `param = 45.0`, the program using a double array returns:
```cpp
sum = 450 000 000.00
```
While the program using a float array returns:
```cpp
sum = 405 682 432.00
```
A ~10% difference!

This task perfectly illustrates the importance of choosing the right type when precision is key.