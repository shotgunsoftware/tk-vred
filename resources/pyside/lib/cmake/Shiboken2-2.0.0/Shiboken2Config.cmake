#  SHIBOKEN_INCLUDE_DIR        - Directories to include to use SHIBOKEN
#  SHIBOKEN_LIBRARY            - Files to link against to use SHIBOKEN
#  SHIBOKEN_BINARY             - Executable name
#  SHIBOKEN_BUILD_TYPE         - Tells if Shiboken was compiled in Release or Debug mode.
#  SHIBOKEN_PYTHON_INTERPRETER - Python interpreter (regular or debug) to be used with the bindings.
#  SHIBOKEN_PYTHON_LIBRARIES   - Python libraries (regular or debug) Shiboken is linked against.

SET(SHIBOKEN_INCLUDE_DIR "C:/pyside/pySide/pyside2_install/py2.7-qt5.6.1-64bit-release/include/shiboken2")
if(MSVC)
    SET(SHIBOKEN_LIBRARY "C:/pyside/pySide/pyside2_install/py2.7-qt5.6.1-64bit-release/lib/shiboken2.lib")
elseif(CYGWIN)
    SET(SHIBOKEN_LIBRARY "C:/pyside/pySide/pyside2_install/py2.7-qt5.6.1-64bit-release/lib/shiboken2.lib")
elseif(WIN32)
    SET(SHIBOKEN_LIBRARY "C:/pyside/pySide/pyside2_install/py2.7-qt5.6.1-64bit-release/bin/shiboken2.dll")
else()
    SET(SHIBOKEN_LIBRARY "C:/pyside/pySide/pyside2_install/py2.7-qt5.6.1-64bit-release/lib/shiboken2.dll")
endif()
SET(SHIBOKEN_PYTHON_INCLUDE_DIR "C:/Python27/include")
SET(SHIBOKEN_PYTHON_INCLUDE_DIR "C:/Python27/include")
SET(SHIBOKEN_PYTHON_INTERPRETER "C:/Python27/python.exe")
SET(SHIBOKEN_PYTHON_VERSION_MAJOR "2")
SET(SHIBOKEN_PYTHON_VERSION_MINOR "7")
SET(SHIBOKEN_PYTHON_VERSION_PATCH "10")
SET(SHIBOKEN_PYTHON_LIBRARIES "C:/Python27/libs/python27.lib")
SET(SHIBOKEN_PYTHON_EXTENSION_SUFFIX "")
message(STATUS "libshiboken built for Release")


set(SHIBOKEN_BINARY "C:/pyside/pySide/pyside2_install/py2.7-qt5.6.1-64bit-release/bin/shiboken2")
