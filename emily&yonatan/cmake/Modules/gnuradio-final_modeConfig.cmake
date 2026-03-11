find_package(PkgConfig)

PKG_CHECK_MODULES(PC_GR_FINAL_MODE gnuradio-final_mode)

FIND_PATH(
    GR_FINAL_MODE_INCLUDE_DIRS
    NAMES gnuradio/final_mode/api.h
    HINTS $ENV{FINAL_MODE_DIR}/include
        ${PC_FINAL_MODE_INCLUDEDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/include
          /usr/local/include
          /usr/include
)

FIND_LIBRARY(
    GR_FINAL_MODE_LIBRARIES
    NAMES gnuradio-final_mode
    HINTS $ENV{FINAL_MODE_DIR}/lib
        ${PC_FINAL_MODE_LIBDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/lib
          ${CMAKE_INSTALL_PREFIX}/lib64
          /usr/local/lib
          /usr/local/lib64
          /usr/lib
          /usr/lib64
          )

include("${CMAKE_CURRENT_LIST_DIR}/gnuradio-final_modeTarget.cmake")

INCLUDE(FindPackageHandleStandardArgs)
FIND_PACKAGE_HANDLE_STANDARD_ARGS(GR_FINAL_MODE DEFAULT_MSG GR_FINAL_MODE_LIBRARIES GR_FINAL_MODE_INCLUDE_DIRS)
MARK_AS_ADVANCED(GR_FINAL_MODE_LIBRARIES GR_FINAL_MODE_INCLUDE_DIRS)
