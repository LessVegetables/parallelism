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
To build only one of the programs, set the respective flag to `ON`:
```sh
cmake .. -DBUILD_DOUBLE=ON
make
```
*or*
```sh
cmake .. -DBUILD_FLOAT=ON
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

The program using a double array returns:
```cpp
sum = -0.00000000067691628
```
While the program using a float array returns:
```cpp
sum = -0.21389430761337280
```
