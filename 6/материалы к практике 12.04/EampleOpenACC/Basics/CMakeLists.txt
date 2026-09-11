cmake_minimum_required(VERSION 3.22)

project(basics_openacc VERSION 1.0 LANGUAGES CXX)

set(CMAKE_CXX_COMPILER "pgc++")
message("Compile C++: " ${CMAKE_CXX_COMPILER})

# Создаём папку для бинарников
set(OUTPUT_DIR ${CMAKE_BINARY_DIR}/bin)
file(MAKE_DIRECTORY ${OUTPUT_DIR})

# Находим все .cpp файлы
file(GLOB SOURCES "*.cpp")

list(APPEND option_compile -acc=gpu -Minfo=all)
list(APPEND option_link -acc=gpu)

# Создаём отдельный исполняемый файл для каждого .cpp файла
foreach(SRC ${SOURCES})
    get_filename_component(EXE_NAME ${SRC} NAME_WE)
    add_executable(${EXE_NAME} ${SRC})
    set_target_properties(${EXE_NAME} PROPERTIES RUNTIME_OUTPUT_DIRECTORY ${OUTPUT_DIR})
    target_compile_features(${EXE_NAME} PRIVATE cxx_std_20)
    # openACC
    target_compile_options(${EXE_NAME} PRIVATE ${option_compile}) 
    target_link_options(${EXE_NAME} PRIVATE ${option_link})
endforeach()
