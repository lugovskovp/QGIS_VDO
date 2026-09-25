# Команда: Запуск тестов QGIS_VDO

## Контекст проекта

- **Интерпретатор:** `C:\OSGeo4W\apps\Python312\python.exe` (Python 3.12.13 из OSGeo4W)
- **НЕ использовать** системный Python `C:\Users\plugo\AppData\Local\Programs\Python\Python313\python.exe`
- **PYTHONPATH:** корень проекта `C:\Work\QGIS_VDO`

## Зависимости

Все установлены в OSGeo4W Python:
- `pytest 9.0.3`
- `bitarray 3.10.0`
- `numpy 2.x`
- `qgis` (родной из OSGeo4W)
- `python-dateutil 2.9.0`


## Запуск

```powershell
cd C:\Work\QGIS_VDO
C:\OSGeo4W\apps\Python312\python.exe -m pytest C:\Work\QGIS_VDO\tests -v --tb=short
```


## Ключевые файлы

| Файл | Описание |
|------|----------|
| `tests/conftest.py` | Фикстуры: `real_vdo_fixture`, `empty_vdo_fixture`, `all_vdo_fixture` |
| `tests/fixtures/__init__.py` | `FIXTURES_DIR`, `BIN_FILES` |
| `vdo/datatypes.py` | Классы VDO_FILE, BYTESTRUCT, BLADDR и др. |
| `vdo/block_base.py` | Базовый класс блоков |
| `vdo/blocks/*.py` | Реализации блоков 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0D, 0x0C, 0x12, 0x13 |

## Известные проблемы

1. **Тесты на одиночные файлы** — требуют физических файлов `.bin` в `tests/fixtures/`.
   Проверяют `os.path.exists(FIXTURES_DIR / filename)` и `pytest.skip`, если файла нет.
