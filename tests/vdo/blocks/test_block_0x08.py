import pytest
from unittest.mock import MagicMock  # , patch

from QGIS_VDO.vdo.datatypes import VDO_FILE
from QGIS_VDO.vdo.geotypes import COORD
from QGIS_VDO.vdo.blocks import block_0x08
from QGIS_VDO.vdo.consts import struct_UINT

from QGIS_VDO.tests.fixtures import FIXTURES_DIR


# --- Настройки окружения и фикстуры ---

#  ee34
# COORD_ORIGIN = COORD(bytes.fromhex('F1193000BC7A5000'))
# COORD_MAX = COORD(bytes.fromhex('511930001C7A5000'))

COORD_ORIGIN = COORD(bytes.fromhex('FDE9F800FC7A5000'))
COORD_MAX = COORD(bytes.fromhex('1DE9F8001C7A5000'))


EXPECTED_TEST_POINTS = {
    "13F919BE13DA074C" : {
        "name": "SPb Peter and Pavel church",
        "coord_str": "59.950064N 30.316605E",
        "map_val_sc_11": 0x09567201,
        "map_val_sc_04": None,
        2: {
            "bl_almanac": 0x05118c01,
            "bl_folder": 0x05119602,
        },
        5: {
            "bl_almanac": 0x0570e601,
            "bl_folder": 0x570e705,
        },
    },
    "1294304B0EB69259" : {
        "name": "Bucarest",
        "coord_str": "44.432300N 26.106300E",
        "map_val_sc_11": 0x09567201,
        "map_val_sc_04": None,
        2: {
            "bl_almanac": 0x05118c01,
            "bl_folder": 0x5119402,
        },
        5: {
            "bl_almanac": 0x0570e601,
            "bl_folder": 0x570e705,
        },
    },
    "EFE7D82403057725" : {
        "name": "out_of_bounds: Panama",
        "coord_str": "9.124172N 78.603348W",
        "map_val_sc_11": None,
        "map_val_sc_04": None,
        2: {
            "bl_almanac": 0x05118c01,
            "bl_folder": None,
        },
        5: {
            "bl_almanac": 0x0570e601,
            "bl_folder": None,
        },
    },
    "1CA8E32908CB0820" : {
        "name": "no item: Hormuz",
        "coord_str": "26.554258N 56.549469E",
        "map_val_sc_11": None,
        "map_val_sc_04": None,
        2: {
            "bl_almanac": 0x05118c01,
            "bl_folder": None,
        },
        5: {
            "bl_almanac": 0x0570e601,
            "bl_folder": 0x570e705,
        },
    },
    "FDE9F800FC7A5000" : {
        "name": "origin: left bottom",
        "coord_str": "10.636742S 36.299691W",
        "map_val_sc_11": 0x55d4805,
        "map_val_sc_04": None,
        2: {
            "bl_almanac": 0x05118c01,
            "bl_folder": None,
        },
        5: {
            "bl_almanac": 0x0570e601,
            "bl_folder": 0x570e705,
        },
    },
    "1DE9F8001C7A5000" : {
        "name": "max: right top",
        "coord_str": "86.000050N 60.337100E",
        "map_val_sc_11": None,
        "map_val_sc_04": None,
        2: {
            "bl_almanac": 0x05118c01,
            "bl_folder": None,
        },
        5: {
            "bl_almanac": 0x0570e601,
            "bl_folder": None,
        },
    },
}


@pytest.fixture(
    scope="function",
    params=list(EXPECTED_TEST_POINTS),
    ids=[EXPECTED_TEST_POINTS[k]["name"] for k in EXPECTED_TEST_POINTS])  # <--- Понятные имена в логах pytest
def point_fixture(request):
    """
    Реальные координаты и проверяемые метрики
    """
    hexcoord = request.param
    coord = COORD(bytes.fromhex(hexcoord))
    metrics = EXPECTED_TEST_POINTS[hexcoord]
    return (coord, metrics)


ALMANAC_DICT = {
    '0x08_ee34_sc2_0x05118c01.bin': {
        "name": "scale 2",
        "scale": 2,
        "item_side": 0x4000000,
        "qty_x": 8,
        "qty_y" : 8,
        "items_cnt": 4,
        "get_xy_item_x": 5,
        "get_xy_item_y": 4,
        "get_xy_item_bl": 0x5119402
    },
    '0x08_ee34_sc5_0x0570e601.bin': {
        "name": "scale 5",
        "scale": 5,
        "item_side": 0x01800000,
        "qty_x": 1,
        "qty_y" : 1,
        "items_cnt": 1,
        "get_xy_item_x": 0,
        "get_xy_item_y": 0,
        "get_xy_item_bl": 0x570e705
    },
}


@pytest.fixture(
    scope="function",
    params=list(ALMANAC_DICT),
    ids=[ALMANAC_DICT[k]["name"] for k in ALMANAC_DICT])
def ru_08_block_fixture(request):
    """
    Фикстура, которая инициализирует реальный блок 0x08 данными из словаря.
    Вместо чтения бинарного файла, мы наполняем его свойствами.
    """
    filename = request.param
    bmetric = ALMANAC_DICT[filename]
    f_path = FIXTURES_DIR / filename

    # Создаем экземпляр класса block_0x08
    empty_vdo = VDO_FILE()
    block = empty_vdo.load_single_block(f_path, 34, 0x200, COORD_ORIGIN, COORD_MAX)

    real_ee_vdo = VDO_FILE(FIXTURES_DIR / 'carindb34_0h_6800h.bin')

    block.vdo = real_ee_vdo

    # # Изолируем внешнюю зависимость vdo
    # block.vdo = MagicMock()
    
    return block, bmetric


def test_coord_from_bytes(point_fixture):
    """ Проверка координат и фикстуры"""
    c, metric = point_fixture

    assert str(c) == metric["coord_str"]


def test_block_0x08_slots_are_effective(ru_08_block_fixture):
    """Проверяем, что оптимизированный block_0x09 жестко держит структуру слотов памяти."""
    block, _ = ru_08_block_fixture

    assert not hasattr(block, '__dict__'), "Обнаружен __dict__! Проверьте __slots__ дочернего класса."
    assert hasattr(block, '__slots__')
    assert 'li_items' in block.__slots__
    assert 'item_side' in block.__slots__
    assert 'origin_hlon' in block.__slots__
    assert 'origin_hlat' in block.__slots__
    assert 'qty_x' in block.__slots__
    assert 'qty_x' in block.__slots__
    """
    __slots__ = (
            'li_items',
            'item_side',
            'origin_hlon',
            'origin_hlat',
            'qty_y',
            'qty_x',
        )
    """


def test_block_0x08_init_unpacks_and_calculates_correctly(ru_08_block_fixture):
    """Проверяем, что __init__ корректно раскладывает COORD на примитивы int и считает сетку."""
    block, metric = ru_08_block_fixture

    # Проверяем распаковку в плоские слоты
    assert block.origin_hlon == -34998272    # 0xf1193000
    assert block.origin_hlat == -59092992    # 0xbc7a5000
    #item_side = 524288
    # Проверяем деление сетки
    assert block.qty_x == metric["qty_x"]
    assert block.qty_y == metric["qty_y"]


def test_block_0x08_items_cnt(ru_08_block_fixture):
    """Проверяем сквозное получение количества элементов из листа валидности."""
    block, metric = ru_08_block_fixture

    assert block.items_cnt() == metric["items_cnt"]


def test_block_0x08_get_items_types(ru_08_block_fixture):
    """Тестируем типы get_items."""
    block, _ = ru_08_block_fixture

    for bk, c1, c2 in block.get_items():

        assert isinstance(bk, int)
        assert isinstance(c1, COORD)
        assert isinstance(c2, COORD)


def test_block_0x08_get_items_doubles(ru_08_block_fixture, point_fixture):
    """Интеграционный тест логики поиска блока по реальным координатам."""
    block, metrics = ru_08_block_fixture

    if metrics["scale"] == 5:   # 1x1 - безсмысленно, если в координатах - то упс
        assert True
    else:
        #
        double_bladdr = struct_UINT.pack(0x10203001)
        ba = bytearray(block._raw)

        block._raw = ba[:0x14] + double_bladdr + double_bladdr + ba[24:]

        with pytest.raises(ValueError, match='Дубликат'):
            _ = [f for f in block.get_items()]


def test_block_0x8__get_xy_value(ru_08_block_fixture):
    """Тестируем точечную выборку гео-блока по ячейке сетки (X, Y)"""
    block, metric = ru_08_block_fixture

    # Успешное извлечение адреса подблока карты
    res_bladdr_value = block._get_xy_value(metric["get_xy_item_x"], metric["get_xy_item_y"])
        
    assert res_bladdr_value is not None
    assert res_bladdr_value == metric["get_xy_item_bl"]


def test_block_0x8__get_xy_value_out_of_bound(ru_08_block_fixture):
    """Тест выхода за границы индексов списка li_items"""
    block, metric = ru_08_block_fixture

    # Координаты (133, 65) на реальной сетке (1х1 и 8х8) гарантированно дадут item_num >= cnt
    assert block._get_xy_value(133, 65) is None
    # 0 - валиден всегда
    assert block._get_xy_value(0, 65) is None
    assert block._get_xy_value(0, -5) is None
    assert block._get_xy_value(133, 0) is None
    assert block._get_xy_value(-133, 0) is None


def test_block_0x8__get_xy_area_out_of_bound(ru_08_block_fixture):
    """Тест выхода за границы индексов списка li_items"""
    block, metric = ru_08_block_fixture

    # Координаты (133, 65) на реальной сетке (1х1 и 8х8) гарантированно дадут item_num >= cnt
    assert block._get_xy_area(133, 65) is None
    # 0 - валиден всегда
    assert block._get_xy_area(0, 65) is None
    assert block._get_xy_area(0, -5) is None
    assert block._get_xy_area(133, 0) is None
    assert block._get_xy_area(-133, 0) is None


def test_get_xy_area_math(ru_08_block_fixture):
    """Отдельный изолированный тест математики метода get_xy_area."""
    block, bmetric = ru_08_block_fixture
    
    # Берем тестовые x и y из вашего ALMANAC_DICT
    tx = bmetric["get_xy_item_x"]
    ty = bmetric["get_xy_item_y"]
    
    # Вызываем реальный метод рассчета координат области ячейки
    lb, rt = block._get_xy_area(tx, ty)
    
    # Проверяем, что вернулись корректные объекты COORD
    assert isinstance(lb, COORD)
    assert isinstance(rt, COORD)
    
    # Проверяем шаг сетки: разница между правым верхним (rt) и левым нижним (lb)
    # по обеим осям должна строго равняться размеру стороны ячейки (item_side)
    assert (rt._hlongitude - lb._hlongitude) == block.item_side
    assert (rt._hlatitude - lb._hlatitude) == block.item_side


def test_block_0x8__get_xy_value_first_empty(ru_08_block_fixture):
    """Тест обработки пустой ячейки (нулевой указатель)"""
    block, metric = ru_08_block_fixture

    bl_value = block._get_xy_value(0, 0)
    
    # 0 - валиден всегда
    if metric["scale"] != 5:        # sc=5 -> 1x1
        assert bl_value is None
    else:
        assert isinstance(bl_value, int)


def test_block_0x08__find_folder_by_coord_integration(ru_08_block_fixture, point_fixture):
    """Интеграционный тест логики поиска блока по реальным координатам."""
    coord_srch, metric = point_fixture
    block, bmetric = ru_08_block_fixture

    # Динамически определяем ожидаемое значение для текущего масштаба блока
    target_value = metric[bmetric["scale"]]["bl_folder"]

    res = block._find_folder_by_coord(coord_srch)

    if res is None:
        assert target_value is None
    else:
        block, lb, rt = res
        assert block.value == target_value
        

def test_block_0x08_find_by_coord_none(ru_08_block_fixture):
    """Test find_by_coord rerurn None if not found"""
    block: block_0x08
    block, metrics = ru_08_block_fixture

    if metrics["scale"] == 5:
        assert True
    else:
        # "1CA8E32908CB0820" : "name": "no item: Hormuz",
        none_srch = COORD(bytes.fromhex("1CA8E32908CB0820"))
        res = block.find_by_coord(none_srch)

        assert res is None


# -----------------------------------------

def test_find_by_coord_extraction_and_forwarding():
    """Тест распаковки b_09, загрузки block_0x09 и вызова его find_by_coord."""
    
    # 1. Создаем пустой объект класса block_0x08 в обход реального __init__
    block = MagicMock(spec=block_0x08)
    block.vdo = MagicMock()
    
    # Ссылаем метод на реальный исполняемый код вашего класса
    block.find_by_coord = block_0x08.find_by_coord.__get__(block, block_0x08)

    # 2. Готовим входные данные и мокаем предыдущий шаг
    srch_coord = MagicMock()  # Фейковый объект COORD для поиска
    
    # Имитируем, что _find_folder_by_coord уже успешно вернул кортеж (bl, c1, c2)
    mock_bl, mock_c1, mock_c2 = "fake_bl", "fake_c1", "fake_c2"
    block._find_folder_by_coord = MagicMock(return_value=(mock_bl, mock_c1, mock_c2))

    # 3. Настраиваем поведение загружаемого блока block_0x09
    expected_result = 0xABCDE  # Финальный BLADDR, который мы ожидаем получить
    mock_bl_folder = MagicMock()
    mock_bl_folder.find_by_coord = MagicMock(return_value=expected_result)
    
    # Инструктируем vdo.get_block вернуть наш настроенный mock_bl_folder
    block.vdo.get_block = MagicMock(return_value=mock_bl_folder)

    # 4. Выполнение целевого участка кода
    actual_result = block.find_by_coord(srch_coord)

    # 5. Проверки (Assertions)
    # Проверяем, что менеджер vdo.get_block вызван с правильными bl, c1, c2 из кортежа
    block.vdo.get_block.assert_called_once_with(mock_bl, mock_c1, mock_c2)
    
    # Проверяем, что у загруженного блока вызван метод find_by_coord с исходной координатой
    mock_bl_folder.find_by_coord.assert_called_once_with(srch_coord)
    
    # Проверяем, что метод вернул именно то значение, которое отдал bl_folder
    assert actual_result == expected_result
