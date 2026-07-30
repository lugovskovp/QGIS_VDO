import pytest   # type: ignore
from pathlib import Path

# __file__ указывает на fixtures/__init__.py, .parent дает путь к папке fixtures
FIXTURES_DIR = Path(__file__).parent

BIN_FILES = [
    "carindb30_0h_9000h.bin",
    "carindb34_0h_6800h.bin",
    "DB34_0h_3A01h.bin"
]


@pytest.fixture(params=BIN_FILES, ids=lambda f: f.split('_')[0])
def bin_file_path(request):
    """Поочередно возвращает Path к каждому из трех bin-файлов"""
    return FIXTURES_DIR / request.param
