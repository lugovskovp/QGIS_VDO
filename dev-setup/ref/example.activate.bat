@echo off

rem This file is UTF-8 encoded, so we need to update the current code page while executing it
for /f "tokens=2 delims=:." %%a in ('"%SystemRoot%\System32\chcp.com"') do (
    set _OLD_CODEPAGE=%%a
)
if defined _OLD_CODEPAGE (
    "%SystemRoot%\System32\chcp.com" 65001 > nul
)

set "VIRTUAL_ENV=c:\Work\QGIS_VDO\.venv"

if not defined PROMPT set PROMPT=$P$G

if defined _OLD_VIRTUAL_PROMPT set PROMPT=%_OLD_VIRTUAL_PROMPT%
if defined _OLD_VIRTUAL_PYTHONHOME set PYTHONHOME=%_OLD_VIRTUAL_PYTHONHOME%

set _OLD_VIRTUAL_PROMPT=%PROMPT%
set PROMPT=(.venv) %PROMPT%

if defined PYTHONHOME set _OLD_VIRTUAL_PYTHONHOME=%PYTHONHOME%
set PYTHONHOME=

if defined _OLD_VIRTUAL_PATH set PATH=%_OLD_VIRTUAL_PATH%
if not defined _OLD_VIRTUAL_PATH set _OLD_VIRTUAL_PATH=%PATH%

set "PATH=%VIRTUAL_ENV%\Scripts;%PATH%"
set "VIRTUAL_ENV_PROMPT=(.venv) "

:END
if defined _OLD_CODEPAGE (
    "%SystemRoot%\System32\chcp.com" %_OLD_CODEPAGE% > nul
    set _OLD_CODEPAGE=
)


:: # Add to the venv envirement vars 
set OSGEO4W_ROOT=c:\OSGeo4W

set CURL_CA_BUNDLE=%OSGEO4W_ROOT%\bin\curl-ca-bundle.crt
SET GDAL_DATA=%OSGEO4W_ROOT%\apps\gdal\share\gdal
SET GDAL_DRIVER_PATH=%OSGEO4W_ROOT%\apps\gdal\lib\gdalplugins
set GS_LIB=%OSGEO4W_ROOT%\apps\gs\lib
set OPENSSL_ENGINES=%OSGEO4W_ROOT%\lib\engines-3
set SSL_CERT_FILE=%OSGEO4W_ROOT%\bin\curl-ca-bundle.crt
set SSL_CERT_DIR=%OSGEO4W_ROOT%\apps\openssl\certs
set PDAL_DRIVER_PATH=%OSGEO4W_ROOT%\apps\pdal\plugins
SET PROJ_DATA=%OSGEO4W_ROOT%\share\proj

@REM PATH %PATH%;%OSGEO4W_ROOT%\apps\qt5\bin;%OSGEO4W_ROOT%\apps\Python312\Scripts;%OSGEO4W_ROOT%\bin;%WINDIR%\system32;%WINDIR%;%WINDIR%\system32\WBem;
PATH %PATH%;%OSGEO4W_ROOT%\apps\qt5\bin;%OSGEO4W_ROOT%\apps\Python312\Scripts;%OSGEO4W_ROOT%\bin;%WINDIR%\system32\WBem;
PATH %OSGEO4W_ROOT%\apps\qgis-ltr\bin;%PATH%

set QT_PLUGIN_PATH=%OSGEO4W_ROOT%\apps\Qt5\plugins
set O4W_QT_PREFIX=%OSGEO4W_ROOT:\=/%/apps/Qt5
set O4W_QT_BINARIES=%OSGEO4W_ROOT:\=/%/apps/Qt5/bin
set O4W_QT_PLUGINS=%OSGEO4W_ROOT:\=/%/apps/Qt5/plugins
set O4W_QT_LIBRARIES=%OSGEO4W_ROOT:\=/%/apps/Qt5/lib
set O4W_QT_TRANSLATIONS=%OSGEO4W_ROOT:\=/%/apps/Qt5/translations
set O4W_QT_HEADERS=%OSGEO4W_ROOT:\=/%/apps/Qt5/include
set O4W_QT_DOC=%OSGEO4W_ROOT:\=/%/apps/Qt5/doc
:: ::

set QGIS_PREFIX_PATH=%OSGEO4W_ROOT:\=/%/apps/qgis-ltr
set GDAL_FILENAME_IS_UTF8=YES
rem Set VSI cache to be used as buffer, see #6448
set VSI_CACHE=TRUE
set VSI_CACHE_SIZE=1000000
set QT_PLUGIN_PATH=%OSGEO4W_ROOT%\apps\qgis-ltr\qtplugins;%OSGEO4W_ROOT%\apps\qt5\plugins

SET PYTHONHOME=%OSGEO4W_ROOT%\apps\Python312
set PYTHONPATH=%OSGEO4W_ROOT%\apps\qgis-ltr\python;
