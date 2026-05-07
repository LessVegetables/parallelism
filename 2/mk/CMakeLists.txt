cmake_minimum_required(VERSION 3.10)
project(openMP1 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_COMPILER g++)

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fopenmp -O2") # Значения по умолчанию

# Создаём папку для бинарников
set(OUTPUT_DIR ${CMAKE_BINARY_DIR}/bin)
file(MAKE_DIRECTORY ${OUTPUT_DIR})

# Включаем поддержку OpenMP
find_package(OpenMP REQUIRED)

# Ищем библиотеку потоков
find_package(Threads REQUIRED)

# Находим все .cpp файлы
file(GLOB SOURCES "*.cpp")

# Создаём отдельный исполняемый файл для каждого .cpp файла
foreach(SRC ${SOURCES})
    get_filename_component(EXE_NAME ${SRC} NAME_WE)
    add_executable(${EXE_NAME} ${SRC})
    set_target_properties(${EXE_NAME} PROPERTIES RUNTIME_OUTPUT_DIRECTORY ${OUTPUT_DIR})
    target_compile_features(${EXE_NAME} PRIVATE cxx_std_17)
    target_link_libraries(${EXE_NAME} PRIVATE Threads::Threads)
endforeach()
