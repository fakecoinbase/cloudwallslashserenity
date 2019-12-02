# This module tries to find libcrypto-mktdata library and include files
#
# LIBCRYPTOMKTDATA_INCLUDE_DIR, path where to find cloudwall/crypto-mkdata/*.h
# LIBCRYPTOMKTDATA_LIBRARY_DIR, path where to find libcrypto-mktdata.a
# LIBCRYPTOMKTDATA_LIBRARIES, the library to link against
# LIBCRYPTOMKTDATA_FOUND, If false, do not try to use libcrypto-mktdata
#
# This currently works probably only for Linux

include(FindPackageHandleStandardArgs)
SET ( LIBCRYPTOMKTDATA_FOUND FALSE )

FIND_PATH ( LIBCRYPTOMKTDATA_INCLUDE_DIR NAMES cloudwall/crypto-mktdata/core.h
        HINTS /usr/local/include /usr/include
        )

FIND_LIBRARY ( LIBCRYPTOMKTDATA_LIBRARIES NAMES libcrypto-mktdata
        HINTS /usr/local/lib /usr/lib
        )

GET_FILENAME_COMPONENT( LIBCRYPTOMKTDATA_LIBRARY_DIR ${LIBCRYPTOMKTDATA_LIBRARIES} PATH )

IF ( LIBCRYPTOMKTDATA_INCLUDE_DIR )
    IF ( LIBCRYPTOMKTDATA_LIBRARIES )
        SET ( LIBCRYPTOMKTDATA_FOUND TRUE )
    ENDIF ( LIBCRYPTOMKTDATA_LIBRARIES )
ENDIF ( LIBCRYPTOMKTDATA_INCLUDE_DIR )


IF ( LIBCRYPTOMKTDATA_FOUND )
    MARK_AS_ADVANCED(
            LIBCRYPTOMKTDATA_LIBRARY_DIR
            LIBCRYPTOMKTDATA_INCLUDE_DIR
            LIBCRYPTOMKTDATA_LIBRARIES
    )
ENDIF ( )

find_package_handle_standard_args(LIBCRYPTOMKTDATA
        DEFAULT_MSG
        LIBCRYPTOMKTDATA_INCLUDE_DIR
        LIBCRYPTOMKTDATA_LIBRARIES)