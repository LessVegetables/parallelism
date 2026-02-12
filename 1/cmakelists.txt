cmake_minimum_required(VERSION 3.10)
project(MyProject CXX)

option(BUILD_DOUBLE "Build executable with 'double' type" OFF)
option(BUILD_FLOAT "Build executable with 'float' type" OFF)

if (NOT (BUILD_DOUBLE OR BUILD_FLOAT))
    set(BUILD_DOUBLE ON)
    set(BUILD_FLOAT ON)
endif()

if (BUILD_DOUBLE)
    add_executable(main_d 1.cpp)
    target_compile_definitions(main_d PRIVATE TYPE=double)
endif()

if (BUILD_FLOAT)
    add_executable(main_f 1.cpp)
    target_compile_definitions(main_f PRIVATE TYPE=float)
endif()


# # Define an option for setting the flag
# set(FLAG_TYPE "" CACHE STRING "Set to 'd' for double or 'f' for float")

# if(FLAG_TYPE STREQUAL "d")
#     add_executable(main_d 1.cpp)
#     target_compile_definitions(main_d PRIVATE TYPE=double)
# elseif(FLAG_TYPE STREQUAL "f")
#     add_executable(main_f 1.cpp)
#     target_compile_definitions(main_f PRIVATE TYPE=float)
# else()
#     message(WARNING "FLAG_TYPE not set or invalid. Use -DFLAG_TYPE=d or -DFLAG_TYPE=f. Compiling both d and f.")
#     add_executable(main_d 1.cpp)
#     target_compile_definitions(main_d PRIVATE TYPE=double)
#     add_executable(main_f 1.cpp)
#     target_compile_definitions(main_f PRIVATE TYPE=float)
# endif()

