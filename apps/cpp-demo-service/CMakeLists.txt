cmake_minimum_required(VERSION 3.20)

project(cpp_demo_service)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include(FetchContent)

FetchContent_Declare(
    asio
    GIT_REPOSITORY https://github.com/chriskohlhoff/asio.git
    GIT_TAG asio-1-32-0
)

FetchContent_MakeAvailable(asio)

set(ASIO_INCLUDE_DIR
    ${asio_SOURCE_DIR}/asio/include
    CACHE PATH "Asio include directory"
)

FetchContent_Declare(
    Crow
    GIT_REPOSITORY https://github.com/CrowCpp/Crow.git
    GIT_TAG v1.3.4
)

FetchContent_MakeAvailable(Crow)

add_executable(cpp-demo-service
    src/main.cpp
)

target_include_directories(cpp-demo-service PRIVATE
    ${ASIO_INCLUDE_DIR}
)

target_link_libraries(cpp-demo-service PRIVATE
    Crow::Crow
    ws2_32
    mswsock
)
