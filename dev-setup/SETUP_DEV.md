# Настройка среды разработки плагинов VSCode+QGIS

## ПО
- Windows 10
- VS Code 1.119.0
- OSGEO4W: QGIS Desctop 3.44.10, Qt5, Python312 (c:\OSGeo4W\)
- QGIS DevTools plugin 
- не надо QGIS debugvs plugin
- QGIS Plugin Reloader
- Разрабатываемый плагин QGIS_VDO (c:\Work\QGIS_VDO\)
- Carindb VDO v.
- Carindb VDO v.

## Теория
0. Установка [QGIS DevTools](https://docs.nextgis.com/docs_ngqgis/source/devtools.html)
1. Для запуска+отладки py файлов в VSCode не системным интерпретатором Python, а идущим в комплекте c OSGEO4W, необходимо, чтобы переменные виртуального окружения были установлены так же, как и при запуске QGIS. Для этого и в ``` activate.bat ``` (из cmd) и в ``` Activate.ps1``` (из vscode и powershell) необходимо обеспечить их инициализацию, референс - **c:\OSGeo4W\bin\python-qgis-ltr.bat**.  
2. PS env set->     ``` $env:PYTHONHOME="c:\OSGeo4W\apps\Python312" ```
3. PS env view->    ``` Get-ChildItem Env: ```
4. PYTHONHOME в виртуальном окружении активацией очищается. В то же время, т.к. при установке pip пакетов необходима эта переменная (иначе ``` Could not find platform independent libraries <prefix> ```), в пакетные файлы добавляю ``` PYTHONHOME=c:\OSGeo4W\apps\Python312 ```.
5. Проверка - ``` .venv\Scripts\activate```, ```pip -V```
Результат:
```
(.venv) c:\Work\QGIS_VDO>pip -V
pip 25.0.1 from c:\Work\QGIS_VDO\.venv\Lib\site-packages\pip (python 3.12)
```

## Последовательность установки среды разработки
Для разработки в VSCode с поддержкой дебага:
1. Создать симлинк из папки разработки планина на папку с плагинами QGIS, с админскими правами.
``` mklink /D "C:\Users\plugo\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\QGIS_VDO" "c:\Work\QGIS_VDO\" ```
2. Запуск батника, формирующего виртуальное окружение, и копирующего пакетные файлы активации и файлы настроек для VSCode. В т.ч. Настройки Flake8 для QGIS, setting.json, launch.json.
``` c:\Work\QGIS_VDO\dev-setup\make_venv.cmd ```
3. Установка pip ``` .venv\Scripts\activate ```, ``` python.exe -m pip install --upgrade pip ```
4. Настройка Flake8 - ``` pip install flake8 flake8-qgis flake8-qt-tr ```
5. В QGIS установить [Инструменты разработки QGIS DevTool](https://plugins.qgis.org/plugins/devtools/). Документация(https://docs.nextgis.com/docs_ngqgis/source/devtools.html)

## use 3rd party modules
To handle 3rd-party pip dependencies in a QGIS plugin, you should either vendor the packages directly inside your plugin directory or programmatically install them using subprocess and pip into a localized folder upon plugin initialization. 
### create lib dir
```c:\work\dir\> md ext_libs```

### install modules
```pip install bitarray -t ./ext_libs```

### Update __init__.py to find the modules
```
import os
import sys

# Get the path to your plugin's 'ext_libs' folder
plugin_dir = os.path.dirname(__file__)
ext_libs_path = os.path.join(plugin_dir, "ext_libs")

# Inject it into the system path if it isn't there already
if ext_libs_path not in sys.path:
    sys.path.insert(0, ext_libs_path)
```



# Полезные линки
- [Отладка плагинов QGIS 3.x на Python в Windows 10 с помощью VS Code](https://gist.github.com/thbaumann/73c873d4c49d8c1add8dc97359cebabe)
- [habr: Создание собственного репозитория плагинов QGIS](https://habr.com/ru/articles/501298/)
- [Пример плагина, с минимальным набором файлов](https://github.com/wonder-sk/qgis-minimal-plugin)
- [Расширенные инструменты разработчика для QGIS. Включают поддержку удаленной отладки через debugpy](https://github.com/nextgis/qgis_devtools)
