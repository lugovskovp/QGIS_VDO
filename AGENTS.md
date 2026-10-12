Данный проект является расширением для QGIS 3.40+ на Python 3.12+, среда настроена на использование C:\OSGeo4W\bin\python.exe.
Пути плагинов и модулей - в ./vscode/settings.json и @qgis.pth

При редактировании файлов настроек, старые строки не удаляй, а комментируй их.

## Коммиты
- Перед отправкой покажи черновик для подтверждения
- В черновиках коммита достаточно только итогового заголовка и описания
- Описание коммитов должно быть на русском языке.
- Для коммитов использовать способ повествования: глаголы прошедшего времени и совершенного вида.
- Для коммитов использовать Angular Commit Message Conventions


# Запуск тестов

## Окружение
- Использовать интерпретатор: `C:\OSGeo4W\bin\python3.exe` (у него есть PyQt5/qgis)
- Переменные из `.env`: `PYTHONPATH=C:\OSGeo4W\apps\qgis-ltr\python`, `PYTHONHOME=C:\OSGeo4W\apps\Python312`

## Команды

### PowerShell 5.1
```powershell
$env:PYTHONPATH="C:\OSGeo4W\apps\qgis-ltr\python"
$env:PYTHONHOME="C:\OSGeo4W\apps\Python312"
C:\OSGeo4W\bin\python.exe -m pytest -v tests/
```

### CMD
```cmd
set PYTHONPATH=C:\OSGeo4W\apps\qgis-ltr\python
set PYTHONHOME=C:\OSGeo4W\apps\Python312
C:\OSGeo4W\bin\python.exe -m pytest -v tests/
```

### VSCode
- Запуск через Test Explorer или команду `Python: Run pytest` — переменные подхватятся из `.env` автоматически.

## Конфигурация pytest
- `cachedir`: `.pytest_cache`
- `rootdir`: `c:\Work\QGIS_VDO`
- `configfile`: `pyproject.toml`



