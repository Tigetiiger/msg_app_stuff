cmake_minimum_required(VERSION 3.22)
project(msg_app_stuff LANGUAGES CXX)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_C_STANDARD 99)

add_executable(msg_app_stuff src/main.cpp)

# conan stuff
find_package(argparse CONFIG REQUIRED)

target_link_libraries(
  msg_app_stuff
  PRIVATE argparse::argparse
