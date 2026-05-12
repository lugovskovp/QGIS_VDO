@echo off

set PLUGIN_SETUP_PATH=c:\Work\QGIS_VDO\dev-setup
set OSGEO4W_ROOT=c:\OSGeo4W

:: :: Шаг 1. Инициализация ENV, from   c:\OSGeo4W\bin\python-qgis-ltr.bat 
set path=%OSGEO4W_ROOT%\bin;%WINDIR%\system32;%WINDIR%;%WINDIR%\system32\WBem;%PATH%
::for %%f in ("%OSGEO4W_ROOT%\etc\ini\*.bat") do call "%%f"
set CURL_CA_BUNDLE=%OSGEO4W_ROOT%\bin\curl-ca-bundle.crt
SET GDAL_DATA=%OSGEO4W_ROOT%\apps\gdal\share\gdal
SET GDAL_DRIVER_PATH=%OSGEO4W_ROOT%\apps\gdal\lib\gdalplugins
set GS_LIB=%OSGEO4W_ROOT%\apps\gs\lib
set OPENSSL_ENGINES=%OSGEO4W_ROOT%\lib\engines-3
set SSL_CERT_FILE=%OSGEO4W_ROOT%\bin\curl-ca-bundle.crt
set SSL_CERT_DIR=%OSGEO4W_ROOT%\apps\openssl\certs
set PDAL_DRIVER_PATH=%OSGEO4W_ROOT%\apps\pdal\plugins
SET PROJ_DATA=%OSGEO4W_ROOT%\share\proj

SET PYTHONPATH=
SET PYTHONUTF8=1
PATH %PATH%;%OSGEO4W_ROOT%\apps\Python312\Scripts;

path %OSGEO4W_ROOT%\apps\qt5\bin;%PATH%
set QT_PLUGIN_PATH=%OSGEO4W_ROOT%\apps\Qt5\plugins
set O4W_QT_PREFIX=%OSGEO4W_ROOT:\=/%/apps/Qt5
set O4W_QT_BINARIES=%OSGEO4W_ROOT:\=/%/apps/Qt5/bin
set O4W_QT_PLUGINS=%OSGEO4W_ROOT:\=/%/apps/Qt5/plugins
set O4W_QT_LIBRARIES=%OSGEO4W_ROOT:\=/%/apps/Qt5/lib
set O4W_QT_TRANSLATIONS=%OSGEO4W_ROOT:\=/%/apps/Qt5/translations
set O4W_QT_HEADERS=%OSGEO4W_ROOT:\=/%/apps/Qt5/include
set O4W_QT_DOC=%OSGEO4W_ROOT:\=/%/apps/Qt5/doc
:: ::
path %OSGEO4W_ROOT%\apps\qgis-ltr\bin;%PATH%
set QGIS_PREFIX_PATH=%OSGEO4W_ROOT:\=/%/apps/qgis-ltr
set GDAL_FILENAME_IS_UTF8=YES
rem Set VSI cache to be used as buffer, see #6448
set VSI_CACHE=TRUE
set VSI_CACHE_SIZE=1000000
set QT_PLUGIN_PATH=%OSGEO4W_ROOT%\apps\qgis-ltr\qtplugins;%OSGEO4W_ROOT%\apps\qt5\plugins

SET PYTHONHOME=%OSGEO4W_ROOT%\apps\Python312
set PYTHONPATH=%OSGEO4W_ROOT%\apps\qgis-ltr\python;

@echo on

:::::::::::::::::::::::::::::::::::
:: Шаг 2. Создание виртуального окружения
cd %PLUGIN_SETUP_PATH%
cd ..

rem python.exe -m venv --system-site-packages .venv
python.exe -m venv .venv
python.exe -c "import pathlib; import qgis; print(str((pathlib.Path(qgis.__file__)/'../..').resolve()))" > .venv\qgis.pth


:::::::::::::::::::::::::::::::::::
:: Шаг 3. Копирование файлов активации и настроек
copy %PLUGIN_SETUP_PATH%\ref\example.activate.bat c:\Work\QGIS_VDO\.venv\Scripts\activate.bat /Y
copy %PLUGIN_SETUP_PATH%\ref\example.Activate.ps1 c:\Work\QGIS_VDO\.venv\Scripts\Activate.ps1 /Y
copy %PLUGIN_SETUP_PATH%\ref\example.flake8 .flake8 /Y
mkdir .vscode
copy %PLUGIN_SETUP_PATH%\ref\example.settings.json .vscode\settings.json /Y
copy %PLUGIN_SETUP_PATH%\ref\example.launch.json .vscode\launch.json /Y


::::::::::::::::::::::::::::::
:::::
:: Шаг 4. Запуск виртуального окружения

::.venv\Scripts\activate
:: python.exe -m pip install --upgrade pip
:: pip install flake8 flake8-qgis flake8-qt-tr 
:: pip install PyQt5 PyQt5-Qt5 PyQt5_sip


:: ???????? pip install debugpy


:: pip install pytest pytest-qgis pytest-cov flake8 flake8-qgis isort
:: pytest, pytest-qgis, pytest-cov — тестирование и покрытие кода;
:: flake8 — базовый линтер Python;
:: flake8-qgis — плагин Flake8 с правилами для кода QGIS;
:: black — автоформатирование кода;
:: isort — автоматическая сортировка импортов.

:::::::::::::::::::::::::::::::::::
:::::::::::::::::::::::::::::::::::
cd %PLUGIN_SETUP%