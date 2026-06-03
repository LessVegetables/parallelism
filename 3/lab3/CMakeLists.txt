cmake_minimum_required(VERSION 3.10)
project(task2 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(Threads REQUIRED)

# Определяем имя компилятора для папки бинарников
if(CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
    set(COMPILER_NAME "g++")
elseif(CMAKE_CXX_COMPILER_ID STREQUAL "Clang")
    set(COMPILER_NAME "clang++")
else()
    set(COMPILER_NAME "unknown")
endif()

set(OUTPUT_DIR ${CMAKE_BINARY_DIR}/bin/${COMPILER_NAME})
file(MAKE_DIRECTORY ${OUTPUT_DIR})

# Основное приложение
add_executable(main main.cpp)
target_link_libraries(main PRIVATE Threads::Threads)
set_target_properties(main PROPERTIES RUNTIME_OUTPUT_DIRECTORY ${OUTPUT_DIR})
target_compile_features(main PRIVATE cxx_std_20)

# Тест
add_executable(test_results test.cpp)
target_link_libraries(test_results PRIVATE Threads::Threads)
set_target_properties(test_results PROPERTIES RUNTIME_OUTPUT_DIRECTORY ${OUTPUT_DIR})
target_compile_features(test_results PRIVATE cxx_std_20)
