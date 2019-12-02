# Install script for directory: /home/kdowney/dev/shadows/libcrypto-mktdata

# Set the install prefix
if(NOT DEFINED CMAKE_INSTALL_PREFIX)
  set(CMAKE_INSTALL_PREFIX "/usr/local")
endif()
string(REGEX REPLACE "/$" "" CMAKE_INSTALL_PREFIX "${CMAKE_INSTALL_PREFIX}")

# Set the install configuration name.
if(NOT DEFINED CMAKE_INSTALL_CONFIG_NAME)
  if(BUILD_TYPE)
    string(REGEX REPLACE "^[^A-Za-z0-9_]+" ""
           CMAKE_INSTALL_CONFIG_NAME "${BUILD_TYPE}")
  else()
    set(CMAKE_INSTALL_CONFIG_NAME "Debug")
  endif()
  message(STATUS "Install configuration: \"${CMAKE_INSTALL_CONFIG_NAME}\"")
endif()

# Set the component getting installed.
if(NOT CMAKE_INSTALL_COMPONENT)
  if(COMPONENT)
    message(STATUS "Install component: \"${COMPONENT}\"")
    set(CMAKE_INSTALL_COMPONENT "${COMPONENT}")
  else()
    set(CMAKE_INSTALL_COMPONENT)
  endif()
endif()

# Install shared libraries without execute permission?
if(NOT DEFINED CMAKE_INSTALL_SO_NO_EXE)
  set(CMAKE_INSTALL_SO_NO_EXE "1")
endif()

# Is this installation the result of a crosscompile?
if(NOT DEFINED CMAKE_CROSSCOMPILING)
  set(CMAKE_CROSSCOMPILING "FALSE")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  list(APPEND CMAKE_ABSOLUTE_DESTINATION_FILES
   "/usr/local/lib/liblibcrypto-mktdata.a")
  if(CMAKE_WARN_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(WARNING "ABSOLUTE path INSTALL DESTINATION : ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  if(CMAKE_ERROR_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(FATAL_ERROR "ABSOLUTE path INSTALL DESTINATION forbidden (by caller): ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
file(INSTALL DESTINATION "/usr/local/lib" TYPE STATIC_LIBRARY FILES "/home/kdowney/dev/shadows/libcrypto-mktdata/cmake-build-debug/lib/liblibcrypto-mktdata.a")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  list(APPEND CMAKE_ABSOLUTE_DESTINATION_FILES
   "/usr/local/include/cloudwall/crypto-mktdata/core.h;/usr/local/include/cloudwall/crypto-mktdata/coinbase.h;/usr/local/include/cloudwall/crypto-mktdata/bitmex.h;/usr/local/include/cloudwall/crypto-mktdata/bitstamp.h;/usr/local/include/cloudwall/crypto-mktdata/kraken.h;/usr/local/include/cloudwall/crypto-mktdata/bitfinex.h;/usr/local/include/cloudwall/crypto-mktdata/binance.h;/usr/local/include/cloudwall/crypto-mktdata/websocket_client.h")
  if(CMAKE_WARN_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(WARNING "ABSOLUTE path INSTALL DESTINATION : ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
  if(CMAKE_ERROR_ON_ABSOLUTE_INSTALL_DESTINATION)
    message(FATAL_ERROR "ABSOLUTE path INSTALL DESTINATION forbidden (by caller): ${CMAKE_ABSOLUTE_DESTINATION_FILES}")
  endif()
file(INSTALL DESTINATION "/usr/local/include/cloudwall/crypto-mktdata" TYPE FILE FILES
    "/home/kdowney/dev/shadows/libcrypto-mktdata/include/cloudwall/crypto-mktdata/core.h"
    "/home/kdowney/dev/shadows/libcrypto-mktdata/include/cloudwall/crypto-mktdata/coinbase.h"
    "/home/kdowney/dev/shadows/libcrypto-mktdata/include/cloudwall/crypto-mktdata/bitmex.h"
    "/home/kdowney/dev/shadows/libcrypto-mktdata/include/cloudwall/crypto-mktdata/bitstamp.h"
    "/home/kdowney/dev/shadows/libcrypto-mktdata/include/cloudwall/crypto-mktdata/kraken.h"
    "/home/kdowney/dev/shadows/libcrypto-mktdata/include/cloudwall/crypto-mktdata/bitfinex.h"
    "/home/kdowney/dev/shadows/libcrypto-mktdata/include/cloudwall/crypto-mktdata/binance.h"
    "/home/kdowney/dev/shadows/libcrypto-mktdata/include/cloudwall/crypto-mktdata/websocket_client.h"
    )
endif()

if(CMAKE_INSTALL_COMPONENT)
  set(CMAKE_INSTALL_MANIFEST "install_manifest_${CMAKE_INSTALL_COMPONENT}.txt")
else()
  set(CMAKE_INSTALL_MANIFEST "install_manifest.txt")
endif()

string(REPLACE ";" "\n" CMAKE_INSTALL_MANIFEST_CONTENT
       "${CMAKE_INSTALL_MANIFEST_FILES}")
file(WRITE "/home/kdowney/dev/shadows/libcrypto-mktdata/cmake-build-debug/${CMAKE_INSTALL_MANIFEST}"
     "${CMAKE_INSTALL_MANIFEST_CONTENT}")
