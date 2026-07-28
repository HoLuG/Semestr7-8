cmake_minimum_required(VERSION 3.20)
project(Lab10)

set(CMAKE_CXX_STANDARD 20)
add_executable(${PROJECT_NAME} main.cpp)

target_include_directories(${PROJECT_NAME}
        PUBLIC
        "D:/Iterpretators/msys/mingw64/include"
        "D:/Iterpretators/msys/mingw64/include/openblas"
)

# Обязательно, чтобы заполнить переменные ${LAPACK_LIBRARIES} и ${BLAS_LIBRARIES}
find_package(BLAS REQUIRED)
find_package(LAPACK REQUIRED)

# Линковка проходит без -llapacke, так как OpenBLAS включает LAPACKE.
target_link_libraries(${PROJECT_NAME}
        ${LAPACK_LIBRARIES}
        ${BLAS_LIBRARIES}
)