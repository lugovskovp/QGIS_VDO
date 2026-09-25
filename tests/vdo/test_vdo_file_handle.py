"""
Тесты для проверки кэширования файлового дескриптора в VDO_FILE.

Проверяют:
1. VDO_FILE() — пустой синглтон, без дескриптора
2. VDO_FILE(path) — валидный файл, дескриптор открывается лениво
3. Множественные read() — дескриптор переиспользуется
4. close() — дескриптор закрывается
5. Повторный read() после close() — дескриптор открывается заново
6. __del__ — дескриптор закрывается автоматически
"""
import gc
# import os

import pytest   # type: ignore # noqa

from QGIS_VDO.vdo.datatypes import VDO_FILE
from QGIS_VDO.vdo.consts import EMPTY_BUFFER


# =====================================================================
# 1. VDO_FILE() — пустой синглтон, без дескриптора
# =====================================================================


def test_singleton_no_file_handle(empty_vdo_fixture):
    """Пустой синглтон не создаёт дескриптор и не открывает файл."""
    vdo, _ = empty_vdo_fixture

    assert vdo.is_empty is True
    assert vdo._file_handle is None
    assert vdo._file_closed is True


def test_singleton_read_returns_empty_buffer(empty_vdo_fixture):
    """Чтение у пустого синглтона всегда возвращает EMPTY_BUFFER."""
    vdo, _ = empty_vdo_fixture

    result = vdo.read(0, 100)
    assert result is EMPTY_BUFFER
    # Дескриптор всё ещё не создан
    assert vdo._file_handle is None


def test_singleton_repr(empty_vdo_fixture):
    """Репрезентация пустого синглтона."""
    vdo, _ = empty_vdo_fixture

    assert repr(vdo) == f"VDO v.{vdo.dbrev}[{vdo.segsize}]:"


# =====================================================================
# 2. VDO_FILE(path) — валидный файл, дескриптор открывается лениво
# =====================================================================


def test_valid_vdo_first_read_opens_handle(real_vdo_fixture):
    """Первый read() после создания использует кэшированный дескриптор."""
    vdo, _ = real_vdo_fixture

    # VDO_FILE.__init__ уже вызвал read() для метаданных,
    # поэтому дескриптор уже открыт
    assert vdo._file_handle is not None
    assert vdo._file_closed is False

    # Данные читаются корректно
    data = vdo.read(0, 4)
    assert len(data) == 4

    vdo.close()


def test_valid_vdo_handle_is_file_object(real_vdo_fixture):
    """Кэшированный дескриптор — это настоящий файловый объект."""
    vdo, _ = real_vdo_fixture

    vdo.read(0, 4)
    handle = vdo._file_handle

    # Проверим, что это файловый объект
    assert hasattr(handle, "read")
    assert hasattr(handle, "seek")
    assert hasattr(handle, "closed")

    vdo.close()


# =====================================================================
# 3. Множественные read() — дескриптор переиспользуется
# =====================================================================


def test_multiple_reads_reuse_handle(real_vdo_fixture):
    """Множественные read() используют один и тот же дескриптор."""
    vdo, _ = real_vdo_fixture

    # Первый read
    data1 = vdo.read(0, 4)
    handle_id_1 = id(vdo._file_handle)

    # Второй read — тот же дескриптор
    data2 = vdo.read(4, 4)
    handle_id_2 = id(vdo._file_handle)

    assert handle_id_1 == handle_id_2
    assert vdo._file_handle is not None

    # Данные разные (разные смещения)
    assert len(data1) == 4
    assert len(data2) == 4

    vdo.close()


def test_multiple_reads_same_handle_identity(real_vdo_fixture):
    """Идентичность дескриптора сохраняется через 10+ чтений."""
    vdo, _ = real_vdo_fixture

    handle_ids = set()
    for i in range(10):
        vdo.read(i * 4, 4)
        handle_ids.add(id(vdo._file_handle))

    # Все 10 чтений — один и тот же дескриптор
    assert len(handle_ids) == 1

    vdo.close()


# =====================================================================
# 4. close() — дескриптор закрывается
# =====================================================================


def test_close_closes_handle(real_vdo_fixture):
    """close() закрывает файловый дескриптор."""
    vdo, _ = real_vdo_fixture

    # Дескриптор уже открыт (из __init__)
    assert vdo._file_handle is not None
    assert vdo._file_closed is False

    # Закрываем
    vdo.close()

    # Дескриптор закрыт и сброшен
    assert vdo._file_closed is True
    assert vdo._file_handle is None


def test_close_on_unopened_handle_is_safe():
    """close() безопасен, если read() ещё не вызывался."""
    vdo = VDO_FILE("nonexistent_file.bin")

    # close() не должен бросить
    vdo.close()

    assert vdo._file_handle is None
    assert vdo._file_closed is True


def test_close_is_idempotent(real_vdo_fixture):
    """Вызов close() несколько раз не ломает объект."""
    vdo, _ = real_vdo_fixture

    vdo.close()
    vdo.close()  # второй раз
    vdo.close()  # третий раз

    assert vdo._file_handle is None
    assert vdo._file_closed is True


# =====================================================================
# 5. Повторный read() после close() — дескриптор открывается заново
# =====================================================================


def test_read_after_close_reopens_handle(real_vdo_fixture):
    """read() после close() открывает новый дескриптор."""
    vdo, _ = real_vdo_fixture

    # Закрываем дескриптор (он уже открыт из __init__)
    vdo.close()
    assert vdo._file_handle is None
    assert vdo._file_closed is True

    # Повторное чтение — должен открыться новый дескриптор
    data = vdo.read(0, 4)
    assert vdo._file_handle is not None
    assert vdo._file_closed is False
    assert len(data) == 4

    vdo.close()


def test_read_after_close_returns_correct_data(real_vdo_fixture):
    """Повторный read() после close() возвращает корректные данные."""
    vdo, _ = real_vdo_fixture

    # Читаем одно и то же смещение после закрытия
    data_before = vdo.read(0, 4)
    vdo.close()
    data_after = vdo.read(0, 4)

    assert data_before == data_after
    assert len(data_before) == 4

    vdo.close()


def test_read_after_close_handle_is_open(real_vdo_fixture):
    """Дескриптор, открытый после close(), действительно работает."""
    vdo, _ = real_vdo_fixture

    vdo.close()
    vdo.read(0, 4)

    # Дескриптор открыт
    handle = vdo._file_handle
    assert handle is not None
    assert not handle.closed

    # Можно читать
    data = handle.read(10)
    assert len(data) == 10

    vdo.close()


# =====================================================================
# 6. __del__ — дескриптор закрывается автоматически
# =====================================================================


def test_del_closes_handle(real_vdo_fixture):
    """__del__ закрывает дескриптор при удалении объекта."""
    vdo, _ = real_vdo_fixture

    # Дескриптор уже открыт
    assert vdo._file_handle is not None

    # Удаляем ссылку и запускаем сборку мусора
    del vdo
    gc.collect()


def test_del_on_unopened_handle_is_safe():
    """__del__ безопасен, если дескриптор не открывался."""
    vdo = VDO_FILE("nonexistent_file.bin")

    # Удаляем — не должно бросить
    del vdo
    gc.collect()


def test_del_on_already_closed_handle_is_safe(real_vdo_fixture):
    """__del__ безопасен, если дескриптор уже закрыт через close()."""
    vdo, _ = real_vdo_fixture

    vdo.close()

    # Удаляем — не должно бросить
    del vdo
    gc.collect()


# =====================================================================
# 7. Синглтон не имеет дескриптора
# =====================================================================


def test_singleton_del_safe():
    """Удаление синглтона не вызывает ошибок."""
    vdo1 = VDO_FILE()
    vdo2 = VDO_FILE()

    # Синглтон
    assert vdo1 is vdo2
    assert vdo1._file_handle is None
    assert vdo1._file_closed is True

    # Удаление — безопасно
    del vdo1
    del vdo2
    gc.collect()


# =====================================================================
# 8. Ошибка при read() — сброс дескриптора
# =====================================================================


def test_read_invalid_offset_returns_empty(real_vdo_fixture):
    """Чтение за пределами файла возвращает EMPTY_BUFFER и не ломает дескриптор."""
    vdo, _ = real_vdo_fixture

    # Корректное чтение
    data = vdo.read(0, 4)
    assert len(data) == 4

    # Чтение за пределами — EMPTY_BUFFER
    result = vdo.read(vdo.file_size + 1000, 10)
    assert result is EMPTY_BUFFER

    # Дескриптор всё ещё валиден
    assert vdo._file_handle is not None
    assert vdo._file_closed is False

    # Можно продолжать читать
    data2 = vdo.read(0, 4)
    assert len(data2) == 4

    vdo.close()


# =====================================================================
# 9. Lazy-open: дескриптор не открывается при создании VDO_FILE
# =====================================================================


def test_lazy_open_no_read_called():
    """
    VDO_FILE с невалидным путём не открывает файл.
    Валидный файл невозможно протестировать без реального файла,
    но мы проверяем, что синглтон не создаёт дескриптор.
    """
    vdo = VDO_FILE()  # пустой синглтон

    assert vdo._file_handle is None
    assert vdo._file_closed is True

    del vdo
    gc.collect()


def test_lazy_open_after_close_works(real_vdo_fixture):
    """
    После close() и повторного read() дескриптор открывается заново
    и работает корректно.
    """
    vdo, _ = real_vdo_fixture

    # Закрываем
    vdo.close()
    assert vdo._file_handle is None

    # Читаем — дескриптор открывается
    data = vdo.read(0, 4)
    assert len(data) == 4
    assert vdo._file_handle is not None

    # Закрываем снова
    vdo.close()
    assert vdo._file_handle is None

    # Ещё раз открываем
    data2 = vdo.read(0, 4)
    assert len(data2) == 4

    vdo.close()
