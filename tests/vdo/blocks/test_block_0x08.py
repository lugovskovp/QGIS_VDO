import pytest
from unittest.mock import MagicMock  # , patch

from QGIS_VDO.vdo.datatypes import VDO_FILE     # , BLADDR
from QGIS_VDO.vdo.geotypes import COORD
# from QGIS_VDO.vdo.blocks import block_0x08
# from QGIS_VDO.vdo.consts import struct_UINT, struct_WORD

from QGIS_VDO.tests.fixtures import FIXTURES_DIR


# --- Настройки окружения и фикстуры ---


# COORD_ORIGIN = COORD(0xf1193000, 0xbc7a5000)
COORD_ORIGIN = COORD(bytes.fromhex('F1193000BC7A5000'))
COORD_MAX = COORD(bytes.fromhex('511930001C7A5000'))


# @pytest.fixture
# def ee_09_block():
#     #  EE sc=7  bl=0x0515a202 lo=317323264 la=326782976; lo=334100480 la=343560192
#     # origin = 58.820952N 27.118204E, max = 61.840852N 30.138103E
#     #item_side = 524288
#     bl_09: block_0x09 = VDO_FILE().load_single_block(FIXTURE_09_FILE, 34, 0x800, COORD_ORIGIN, COORD_MAX)
#     return bl_09


EXPECTED_TEST_POINTS = {
    "13F919BE13DA074C" : {
        "name": "СПб, Петропавловский собор",
        "coord_str": "59.950064N 30.316605E",
        "map_val_sc_11": 0x09567201,
        "map_val_sc_04": None,
    },
    "EFE7D82403057725" : {
        "name": "out_of_bounds: Panama",
        "coord_str": "9.124172N 78.603348W",
        "map_val_sc_11": None,
        "map_val_sc_04": None,
    },
    "1CA8E32908CB0820" : {
        "name": "no item: Ормуз",
        "coord_str": "26.554258N 56.549469E",
        "map_val_sc_11": None,
        "map_val_sc_04": None,
    },
    "F1193000BC7A5000" : {
        "name": "origin: left bottom",
        "coord_str": "203.910324S 75.001372W",
        "map_val_sc_11": 0x55d4805,
        "map_val_sc_04": None,
    },
    "511930001C7A5000" : {
        "name": "max: right top",
        "coord_str": "86.000050N 214.909002E",
        "map_val_sc_11": None,
        "map_val_sc_04": None,
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
    '0x08_ru34_sc04_06205021.bin': {
        "name": "scale 4",
        "scale": 4,
        "item_side": 0x60000000,
        "qty_x": 64,
        "qty_y" : 64,
        "items_cnt": 125,
        "get_xy_item_x": 53,
        "get_xy_item_y": 15,
        "get_xy_item_bl": 0x6207601
    },
    '0x08_ru34_sc11_09567101.bin': {
        "name": "scale 11",
        "scale": 11,
        "item_side": 0x01800000,
        "qty_x": 1,
        "qty_y" : 1,
        "items_cnt": 1,
        "get_xy_item_x": 0,
        "get_xy_item_y": 0,
        "get_xy_item_bl": 0x9567201
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

    # Создаем экземпляр вашего класса block_0x08
    empty_vdo = VDO_FILE()
    block = empty_vdo.load_single_block(f_path, 34, 0x200, COORD_ORIGIN, COORD_MAX)
    
    # Изолируем внешнюю зависимость vdo
    block.vdo = MagicMock()
    
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
    assert 'origin_hlon' in block.__slots__
    assert 'origin_hlat' in block.__slots__
    assert 'qty_x' in block.__slots__


def test_block_0x09_init_unpacks_and_calculates_correctly(ru_08_block_fixture):
    """Проверяем, что __init__ корректно раскладывает COORD на примитивы int и считает сетку."""
    block, metric = ru_08_block_fixture

    # Проверяем распаковку в плоские слоты
    assert block.origin_hlon == -250007552    # 0xf1193000
    assert block.origin_hlat == -1132834816   # 0xbc7a5000
    #item_side = 524288
    # Проверяем деление сетки
    assert block.qty_x == metric["qty_x"]
    assert block.qty_y == metric["qty_y"]


def test_block_0x08_items_cnt(ru_08_block_fixture):
    """Проверяем сквозное получение количества элементов из листа валидности."""
    block, metric = ru_08_block_fixture

    assert block.items_cnt() == metric["items_cnt"]


def test_block_0x08_get_xy_item(ru_08_block_fixture, monkeypatch):
    """Тестируем точечную выборку гео-блока по ячейке сетки (X, Y)."""
    block, metric = ru_08_block_fixture

    # 1. Создаем мок для vdo и настраиваем метод get_bladdr
    mock_vdo = MagicMock()
    
    def mock_get_bladdr(bladdr_val):
        # Создаем мок-объект, имитирующий структуру BLADDR
        mock_res = MagicMock()
        if bladdr_val == 0:
            mock_res.isZero = True
            mock_res.value = 0
        else:
            mock_res.isZero = False
            mock_res.value = bladdr_val
        return mock_res

    mock_vdo.get_bladdr.side_effect = mock_get_bladdr

    # 2. ПОДМЕНЯЕМ vdo НА УРОВНЕ КЛАССА
    # Благодаря этому обходим ограничения __slots__ на экземпляре block
    monkeypatch.setattr(type(block), "vdo", mock_vdo)

    # ==========================================
    # ТЕСТ 1: Успешное извлечение адреса подблока карты
    # ==========================================
    # Метод сам прочитает реальные данные из self._raw, распакует их
    # и передаст правильный bladdr_val в наш mock_get_bladdr
    res_bladdr = block.get_xy_item(metric["get_xy_item_x"], metric["get_xy_item_y"])
    
    assert res_bladdr is not None
    assert res_bladdr.value == metric["get_xy_item_bl"]
    mock_vdo.get_bladdr.assert_called_with(metric["get_xy_item_bl"])

    # ==========================================
    # ТЕСТ 2: Тест выхода за границы индексов списка li_items
    # ==========================================
    # Координаты (133, 5) на реальной сетке гарантированно дадут item_num >= cnt
    assert block.get_xy_item(133, 65) is None

    # ==========================================
    # ТЕСТ 3: Тест обработки пустой ячейки (нулевой указатель)
    # ==========================================
    # Координаты (0, 1) на реальной карте ведут на пустую область,
    # unpack_from вернет 0, и метод вернет None без вызова vdo.get_bladdr
    assert block.get_xy_item(0, 1) is None


def test_block_0x08_get_items_types(ru_08_block_fixture):
    """Тестируем типы get_items."""
    block, _ = ru_08_block_fixture
    for bk, c1, c2 in block.get_items():

        assert isinstance(bk, int)
        assert isinstance(c1, COORD)
        assert isinstance(c2, COORD)


def test_get_xy_area_math(ru_08_block_fixture):
    """Отдельный изолированный тест математики метода get_xy_area."""
    block, bmetric = ru_08_block_fixture
    
    # Берем тестовые x и y из вашего ALMANAC_DICT
    tx = bmetric["get_xy_item_x"]
    ty = bmetric["get_xy_item_y"]
    
    # Вызываем реальный метод рассчета координат области ячейки
    lb, rt = block.get_xy_area(tx, ty)
    
    # Проверяем, что вернулись корректные объекты COORD
    assert isinstance(lb, COORD)
    assert isinstance(rt, COORD)
    
    # Проверяем шаг сетки: разница между правым верхним (rt) и левым нижним (lb)
    # по обеим осям должна строго равняться размеру стороны ячейки (item_side)
    assert (rt._hlongitude - lb._hlongitude) == block.item_side
    assert (rt._hlatitude - lb._hlatitude) == block.item_side


def test_block_0x08_find_by_coord_integration(ru_08_block_fixture, point_fixture, monkeypatch):
    """Интеграционный тест логики поиска блока по реальным координатам."""
    coord_srch, metric = point_fixture
    block, bmetric = ru_08_block_fixture

    # 1. Динамически определяем ожидаемое значение для текущего масштаба блока
    expected_metrix_map = {
        4: "map_val_sc_04",
        11: "map_val_sc_11"
    }
    metric_key = expected_metrix_map[bmetric["scale"]]
    target_value = metric[metric_key]

    # 2. Логика заглушки для get_xy_item
    def mock_get_xy_item(self, x, y):  # Обязательно добавляем self, так как подменяем метод класса!
        if "out_of_bounds" in metric["name"] or "no item" in metric["name"]:
            return None
        return bmetric["get_xy_item_bl"]

    # ИСПОЛЬЗУЕМ monkeypatch ДЛЯ ПОДМЕНЫ НА УРОВНЕ КЛАССА
    # type(block) вернет сам класс block_0x08..
    monkeypatch.setattr(type(block), "get_xy_item", mock_get_xy_item)

    # 3. Настраиваем заглушку для block_0x09
    mock_block_0x09 = MagicMock()
    if target_value is None:
        mock_block_0x09.find_by_coord.return_value = None
    else:
        mock_final_result = MagicMock()
        mock_final_result.value = target_value
        mock_block_0x09.find_by_coord.return_value = mock_final_result

    # Мокаем свойство vdo.get_block у экземпляра
    # Если vdo тоже read-only, используем: monkeypatch.setattr(type(block), "vdo", MagicMock())
    block.vdo.get_block.return_value = mock_block_0x09

    # 4. ВЫЗОВ РЕАЛЬНОГО МЕТОДА (Математика Python-кода выполнится полностью)
    map_bl = block.find_by_coord(coord_srch)

    # 5. ПРОВЕРКИ
    if target_value is None:
        assert map_bl is None
    else:
        assert map_bl is not None
        assert map_bl.value == target_value


def test_block_0x08_find_by_coord_integration_real(ru_08_block_fixture, point_fixture, monkeypatch):
    """Интеграционный тест поиска подблока по реальной бинарной фикстуре."""
    coord_srch, metric = point_fixture
    block, bmetric = ru_08_block_fixture

    # 1. Динамически определяем ожидаемое значение (scale 4 или 11)
    expected_metrix_map = {
        4: "map_val_sc_04",
        11: "map_val_sc_11"
    }
    metric_key = expected_metrix_map[bmetric["scale"]]
    target_value = metric[metric_key]

    # 2. Мокаем vdo (так как vdo объявлен в родителе block_base, подменяем у типа)
    mock_vdo = MagicMock()
    
    # Настраиваем vdo.get_bladdr для вложенного вызова get_xy_item
    def mock_get_bladdr(bladdr_val):
        mock_res = MagicMock()
        mock_res.isZero = (bladdr_val == 0)
        mock_res.value = bladdr_val
        return mock_res
    mock_vdo.get_bladdr.side_effect = mock_get_bladdr

    # Настраиваем цепочку vdo.get_block -> block_0x09
    mock_block_0x09 = MagicMock()
    if target_value is None:
        mock_block_0x09.find_by_coord.return_value = None
    else:
        mock_final_block = MagicMock()
        mock_final_block.value = target_value
        mock_block_0x09.find_by_coord.return_value = mock_final_block
        
    mock_vdo.get_block.return_value = mock_block_0x09

    # Внедряем мок vdo, обходя ограничения __slots__
    monkeypatch.setattr(type(block), "vdo", mock_vdo)

    # 3. ВЫЗОВ ОРИГИНАЛЬНОГО МЕТОДА (Выполняется вся математика с MOST_SIGNIFICANT_BIT)
    map_bl = block.find_by_coord(coord_srch)

    # 4. ПРОВЕРКИ
    if target_value is None:
        assert map_bl is None
    else:
        assert map_bl is not None
        assert map_bl.value == target_value
