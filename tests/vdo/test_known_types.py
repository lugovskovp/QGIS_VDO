import pytest   # type: ignore # noqa
import os

from QGIS_VDO.vdo.datatypes import setup_known_types


def test_setup_known_types_dynamic_parsing(tmp_path):
    """Тест проверяет, что функция корректно парсит имена файлов разной длины и игнорирует мусор."""
    # Создаем временную папку blocks
    test_blocks_dir = tmp_path / "blocks"
    test_blocks_dir.mkdir()
    
    # Создаем фейковые файлы блоков с разной длиной HEX
    (test_blocks_dir / "block_0x0B.py").write_text("# fake block 11")
    (test_blocks_dir / "block_0x100.py").write_text("# fake block 256")
    (test_blocks_dir / "block_invalid.py").write_text("# мусорный файл, должен игнорироваться")
    (test_blocks_dir / "some_other_file.txt").write_text("# не питоновский файл")

    # Вызываем функцию, передавая ей изолированную временную папку
    result_dict = setup_known_types(blocks_dir=str(test_blocks_dir))
    
    # Проверяем, что словарь собрался правильно
    assert 11 in result_dict
    assert result_dict[11] == "block_0x0B"
    
    # Проверяем, что трехзначный HEX (0x100 = 256) тоже распарсился корректно (старый код бы тут упал)
    assert 256 in result_dict
    assert result_dict[256] == "block_0x100"
    
    # Проверяем, что лишние файлы не попали в словарь
    assert len(result_dict) == 2


def test_setup_known_types_non_exist_path():
    #
    non_exists_path = "lkmdzkjnsvkjnsdjkns"
    result_dict = setup_known_types(blocks_dir=non_exists_path)

    assert result_dict == {}


def test_setup_known_types_returns_empty_dict_on_os_error(monkeypatch):
    """
    Проверяет, что если при чтении директории возникает OSError (например, PermissionError),
    функцияsetup_known_types не падает, а безопасно возвращает пустой словарь.
    """
    # 1. Задаем фейковый существующий путь, чтобы пройти проверку os.path.exists
    fake_dir = "/fake/existing/blocks/dir"
    
    # Подменяем os.path.exists, чтобы он вернул True для нашей фейковой папки
    monkeypatch.setattr(os.path, "exists", lambda path: path == fake_dir or os.path.exists(path))

    # 2. Имитируем системную ошибку внутри os.listdir
    def mock_listdir(path):
        if path == fake_dir:
            # Бросаем стандартное системное исключение (наследник OSError)
            raise PermissionError("[Errno 13] Permission denied")
        return os.listdir(path)

    monkeypatch.setattr(os, "listdir", mock_listdir)

    # 3. Вызываем тестируемую функцию
    # Замените путь импорта setup_known_types на ваш актуальный
    result = setup_known_types(blocks_dir=fake_dir)

    # 4. Проверяем, что исключение перехвачено и возвращен пустой словарь
    assert result == {}
    assert isinstance(result, dict)
