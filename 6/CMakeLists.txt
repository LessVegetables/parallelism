cmake_minimum_required(VERSION 3.18)
project(heat_equation CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# pgc++ from NVIDIA HPC SDK is required
set(CMAKE_CXX_COMPILER pgc++)
message(STATUS "Compiler: ${CMAKE_CXX_COMPILER}")

# OpenACC target: host | multicore | gpu  (override with -DACC_TARGET=...)
set(ACC_TARGET "gpu" CACHE STRING "OpenACC target: host, multicore, gpu")
message(STATUS "ACC target: ${ACC_TARGET}")

# Boost
find_package(Boost REQUIRED COMPONENTS program_options)

# CUDA toolkit (for NVTX markers, optional)
find_package(CUDAToolkit QUIET)

# Compiler / linker flags
set(ACC_FLAGS -acc=${ACC_TARGET} -Minfo=all)

add_executable(heat_eq main.cpp)

target_compile_options(heat_eq PRIVATE ${ACC_FLAGS})
target_link_options(heat_eq PRIVATE ${ACC_FLAGS})

target_link_libraries(heat_eq PRIVATE Boost::program_options)

if(CUDAToolkit_FOUND)
    target_compile_definitions(heat_eq PRIVATE USE_NVTX)
    target_include_directories(heat_eq PRIVATE ${CUDAToolkit_INCLUDE_DIRS})
    target_link_libraries(heat_eq PRIVATE CUDA::nvToolsExt)
    message(STATUS "NVTX markers enabled")
else()
    message(STATUS "CUDAToolkit not found — NVTX markers disabled")
endif()

# Convenience targets for all three ACC modes
foreach(TARGET_MODE host multicore gpu)
    add_executable(heat_eq_${TARGET_MODE} main.cpp)
    target_compile_options(heat_eq_${TARGET_MODE} PRIVATE -acc=${TARGET_MODE} -Minfo=all)
    target_link_options(heat_eq_${TARGET_MODE}    PRIVATE -acc=${TARGET_MODE})
    target_link_libraries(heat_eq_${TARGET_MODE}  PRIVATE Boost::program_options)
    if(CUDAToolkit_FOUND)
        target_compile_definitions(heat_eq_${TARGET_MODE} PRIVATE USE_NVTX)
        target_include_directories(heat_eq_${TARGET_MODE} PRIVATE ${CUDAToolkit_INCLUDE_DIRS})
        target_link_libraries(heat_eq_${TARGET_MODE} PRIVATE CUDA::nvToolsExt)
    endif()
endforeach()
