cmake_minimum_required(VERSION 3.10)
project(MyProject CXX)

add_executable(my_exe 1.cpp)

# Define an option for setting the flag
set(FLAG_TYPE "" CACHE STRING "Set to 'd' for double or 'f' for float")

if(FLAG_TYPE STREQUAL "d")
    target_compile_definitions(my_exe PRIVATE TYPE=double)
elseif(FLAG_TYPE STREQUAL "f")
    target_compile_definitions(my_exe PRIVATE TYPE=float)
else()
    message(WARNING "FLAG_TYPE not set or invalid. Use -DFLAG_TYPE=d or -DFLAG_TYPE=f")
endif()
