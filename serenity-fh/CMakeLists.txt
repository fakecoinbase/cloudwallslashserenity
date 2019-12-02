cmake_minimum_required(VERSION 3.14)
project(serenity-fh C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

set(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} "${CMAKE_SOURCE_DIR}/cmake")

include(conan.cmake)

conan_add_remote(NAME bincrafters INDEX 1
        URL https://api.bintray.com/conan/bincrafters/public-conan)
conan_add_remote(NAME LunarWatcher INDEX 2
        URL https://api.bintray.com/conan/oliviazoe0/conan-packages)
conan_cmake_run(REQUIRES boost/1.70.0@conan/stable
                         cppzmq/4.4.1@bincrafters/stable
                         date/2.4.1@bincrafters/stable
                         fmt/5.3.0@bincrafters/stable
                         rapidjson/1.1.0@bincrafters/stable
                         rxcpp/4.1.0@bincrafters/stable
                         spdlog/1.3.1@bincrafters/stable
                         gtest/1.8.1@bincrafters/stable
                         IXWebSocket/5.0.6@LunarWatcher/stable
                         OpenSSL/1.1.1d@conan/stable
        BASIC_SETUP BUILD missing)

find_package(LibCryptoMktData REQUIRED)
find_package(CapnProto REQUIRED)

include_directories(include ${LIBCRYPTOMKTDATA_INCLUDE_DIR} ${LIBIXWEBSOCKET_INCLUDE_DIR} ${CAPNP_INCLUDE_DIRS})
set(LIBS ${LIBS} ${CONAN_LIBS} ${LIBCRYPTOMKTDATA_LIBRARIES} ${LIBIXWEBSOCKET_LIBRARIES} ${CAPNP_LIBRARIES})

list(REMOVE_ITEM LIBS boost_unit_test_framework)

add_executable(serenity-fh-coinbase capnp/serenity-fh.capnp.c++ src/coinbase_main.cpp)
target_link_libraries(serenity-fh-coinbase ${LIBS})
if (APPLE)
    target_link_libraries(serenity-fh-coinbase "-framework foundation" "-framework security")
endif()
