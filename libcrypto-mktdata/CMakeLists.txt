cmake_minimum_required(VERSION 3.7)
project(libcrypto-mktdata C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

set(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} "${CMAKE_SOURCE_DIR}/cmake")

include(conan.cmake)

conan_add_remote(NAME bincrafters INDEX 1
        URL https://api.bintray.com/conan/bincrafters/public-conan)
conan_add_remote(NAME LunarWatcher INDEX 2
        URL https://api.bintray.com/conan/oliviazoe0/conan-packages)
conan_cmake_run(REQUIRES date/2.4.1@bincrafters/stable
                         fmt/5.3.0@bincrafters/stable
                         gtest/1.8.1@bincrafters/stable
                         rapidjson/1.1.0@bincrafters/stable
                         spdlog/1.3.1@bincrafters/stable
                         websocketpp/0.8.1@bincrafters/stable
                         IXWebSocket/5.0.6@LunarWatcher/stable
        BASIC_SETUP BUILD missing)

set(LIBCRYPTOMKTDATA_SOURCES
        src/core.cpp
        src/coinbase.cpp
        src/bitmex.cpp
        src/bitstamp.cpp
        src/kraken.cpp
        src/bitfinex.cpp
        src/binance.cpp
        src/websocket_client.cpp
        )

set(LIBCRYPTOMKTDATA_HEADERS
        include/cloudwall/crypto-mktdata/core.h
        include/cloudwall/crypto-mktdata/coinbase.h
        include/cloudwall/crypto-mktdata/bitmex.h
        include/cloudwall/crypto-mktdata/bitstamp.h
        include/cloudwall/crypto-mktdata/kraken.h
        include/cloudwall/crypto-mktdata/bitfinex.h
        include/cloudwall/crypto-mktdata/binance.h
        include/cloudwall/crypto-mktdata/websocket_client.h)

include_directories(include})
set(LIBS ${LIBS} ${CONAN_LIBS})
list(REMOVE_ITEM LIBS boost_unit_test_framework)

add_library(libcrypto-mktdata ${LIBCRYPTOMKTDATA_SOURCES} ${LIBCRYPTOMKTDATA_HEADERS})

add_executable(libcrypto-mktdata_test test/core_test.cpp test/coinbase_test.cpp test/bitmex_test.cpp
        test/bitstamp_test.cpp test/kraken_test.cpp test/bitfinex_test.cpp test/binance_test.cpp)

add_executable(print_client_tls src/print_client_tls.cpp)
target_link_libraries(print_client_tls libcrypto-mktdata ${LIBS})

target_link_libraries(libcrypto-mktdata_test libcrypto-mktdata ${LIBS})
if (APPLE)
    target_link_libraries(libcrypto-mktdata_test "-framework foundation" "-framework security")
endif()

target_include_directories(libcrypto-mktdata PUBLIC ./include)
set_target_properties(libcrypto-mktdata PROPERTIES PUBLIC_HEADER "${LIBCRYPTOMKTDATA_HEADERS}")
install(TARGETS libcrypto-mktdata
        ARCHIVE DESTINATION ${CMAKE_INSTALL_PREFIX}/lib
        PUBLIC_HEADER DESTINATION ${CMAKE_INSTALL_PREFIX}/include/cloudwall/crypto-mktdata)

