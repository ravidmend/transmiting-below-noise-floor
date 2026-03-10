find_package(PkgConfig)

PKG_CHECK_MODULES(PC_GR_HACKATHON gnuradio-hackathon)

FIND_PATH(
    GR_HACKATHON_INCLUDE_DIRS
    NAMES gnuradio/hackathon/api.h
    HINTS $ENV{HACKATHON_DIR}/include
        ${PC_HACKATHON_INCLUDEDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/include
          /usr/local/include
          /usr/include
)

FIND_LIBRARY(
    GR_HACKATHON_LIBRARIES
    NAMES gnuradio-hackathon
    HINTS $ENV{HACKATHON_DIR}/lib
        ${PC_HACKATHON_LIBDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/lib
          ${CMAKE_INSTALL_PREFIX}/lib64
          /usr/local/lib
          /usr/local/lib64
          /usr/lib
          /usr/lib64
          )

include("${CMAKE_CURRENT_LIST_DIR}/gnuradio-hackathonTarget.cmake")

INCLUDE(FindPackageHandleStandardArgs)
FIND_PACKAGE_HANDLE_STANDARD_ARGS(GR_HACKATHON DEFAULT_MSG GR_HACKATHON_LIBRARIES GR_HACKATHON_INCLUDE_DIRS)
MARK_AS_ADVANCED(GR_HACKATHON_LIBRARIES GR_HACKATHON_INCLUDE_DIRS)
