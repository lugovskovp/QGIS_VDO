@echo off
chcp 65001 > nul

:: Путь к целевой директории
set "TARGET_DIR=c:\BACKUPS\QGIS_VDO.git"

:: Проверка существования директории
if not exist "%TARGET_DIR%" (
    echo [INFO] Директория не найдена. Начинаю клонирование...
    git clone --mirror "file:///C:/Work/QGIS_VDO" "%TARGET_DIR%"
) else (
    echo [INFO] Директория уже существует. Выполняю обновление...
    cd /d "%TARGET_DIR%"
    git fetch --all --prune
)

echo [INFO] Работа завершена.
:: pause
