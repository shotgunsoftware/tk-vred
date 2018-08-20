#  PYSIDE_INCLUDE_DIR   - Directories to include to use PySide2
#  PYSIDE_LIBRARY       - Files to link against to use PySide2
#  PYSIDE_PYTHONPATH    - Path to where the PySide2 Python module files could be found
#  PYSIDE_TYPESYSTEMS   - Type system files that should be used by other bindings extending PySide2

SET(PYSIDE_INCLUDE_DIR "C:/pyside/pySide/pyside2_install/py2.7-qt5.6.1-64bit-release/include/PySide2")
# Platform specific library names
if(MSVC)
    SET(PYSIDE_LIBRARY "C:/pyside/pySide/pyside2_install/py2.7-qt5.6.1-64bit-release/lib/pyside2.lib")
elseif(CYGWIN)
    SET(PYSIDE_LIBRARY "C:/pyside/pySide/pyside2_install/py2.7-qt5.6.1-64bit-release/lib/pyside2.lib")
elseif(WIN32)
    SET(PYSIDE_LIBRARY "C:/pyside/pySide/pyside2_install/py2.7-qt5.6.1-64bit-release/bin/pyside2.dll")
else()
    SET(PYSIDE_LIBRARY "C:/pyside/pySide/pyside2_install/py2.7-qt5.6.1-64bit-release/lib/pyside2.dll")
endif()
SET(PYSIDE_PYTHONPATH "C:/pyside/pySide/pyside2_install/py2.7-qt5.6.1-64bit-release/Lib/site-packages")
SET(PYSIDE_TYPESYSTEMS "C:/pyside/pySide/pyside2_install/py2.7-qt5.6.1-64bit-release/share/PySide2/typesystems")
