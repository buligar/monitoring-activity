cmake_minimum_required(VERSION 3.26)
project(client)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_EXE_LINKER_FLAGS "-static")
set(BOOST_ROOT "boost_1_83_0")

find_package(Boost REQUIRED)
include_directories(${Boost_INCLUDE_DIRS})

add_executable(client client.cpp)
target_link_libraries(client wsock32 ws2_32 ${Boost_LIBRARIES})
