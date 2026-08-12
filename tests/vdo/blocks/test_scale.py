import pytest
from unittest.mock import MagicMock  # , patch

from QGIS_VDO.vdo.blocks.block_0x07 import SCALE
from QGIS_VDO.vdo.datatypes import BLADDR, VDO_FILE
from QGIS_VDO.vdo.geotypes import COORD

from QGIS_VDO.tests.fixtures import FIXTURES_DIR


# --- Настройки окружения и фикстуры ---


# EXPECTED_TEST_POINTS = {
#     "13F919BE13DA074C" : {
#         "name": "СПб, Петропавловский собор",
#         "coord_str": "59.950064N 30.316605E",
#         "map_val_sc_11": 0x09567201,
#         "map_val_sc_04": None,
#     },
#     "EFE7D82403057725" : {
#         "name": "out_of_bounds: Panama",
#         "coord_str": "9.124172N 78.603348W",
#         "map_val_sc_11": None,
#         "map_val_sc_04": None,
#     },
#     "F1193000BC7A5000" : {
#         "name": "origin: left bottom",
#         "coord_str": "203.910324S 75.001372W",
#         "map_val_sc_11": 0x55d4805,
#         "map_val_sc_04": None,
#     },
#     "511930001C7A5000" : {
#         "name": "max: right top",
#         "coord_str": "86.000050N 214.909002E",
#         "map_val_sc_11": None,
#         "map_val_sc_04": None,
#     },
# }


# @pytest.fixture(
#     scope="function",
#     params=list(EXPECTED_TEST_POINTS),
#     ids=[EXPECTED_TEST_POINTS[k]["name"] for k in EXPECTED_TEST_POINTS])  # <--- Понятные имена в логах pytest
# def point_fixture(request):
#     """
#     Реальные координаты и проверяемые метрики
#     """
#     hexcoord = request.param
#     coord = COORD(bytes.fromhex(hexcoord))
#     metrics = EXPECTED_TEST_POINTS[hexcoord]
#     return (coord, metrics)


# ru34_sc10 = '094f9401f1193000bc7a5000511930001c7a5000000004b00bb80000'
# bmw34_sc07 = '04d34509f76d9000bc7a5000576d90001c7a50000002000100280000'
# bmw34_sc08 = b'\x00' * 28
# ru30 = '0386d4010000a800f5cd65002800a8001dcd650000020028'

SCALE_DICT = {
    'ru34_sc10': {
        "name": "ru34_sc10",
        "dbrev": 34,
        "segsize": 0x200,
        "bin": '094f9401f1193000bc7a5000511930001c7a5000000004b00bb80000',
        "size": 28,
        "zoom_from": 1200,
        "zoom_to": 3000,
        "value_a": 0,
        "repr": "lat:289.91° x lon:289.91°",
        "repr_alm": "094f94 01",
        "is_empty": False,
    },
    'bmw34_sc07': {
        "name": "bmw34_sc07",
        "dbrev": 34,
        "segsize": 0x200,
        "bin": '04d34509f76d9000bc7a5000576d90001c7a50000002000100280000',
        "size": 28,
        "zoom_from": 1,
        "zoom_to": 40,
        "value_a": 2,
        "repr": "lat:289.91° x lon:289.91°",
        "repr_alm": "04d345 09",
        "is_empty": False,
    },
    'bmw34_sc08': {
        "name": "bmw34_sc08",
        "dbrev": 34,
        "segsize": 0x200,
        "bin": '00' * 28,
        "size": 28,
        "zoom_from": 0,
        "zoom_to": 0,
        "value_a": 0,
        "repr": 'lat:0.00° x lon:0.00°',
        "repr_alm": "000000 00",
        "is_empty": True,
    },
    'ru30_sc6': {
        "name": "ru30_sc6",
        "dbrev": 30,
        "segsize": 0x800,
        "bin": '0386d4010000a800f5cd65002800a8001dcd650000020028',
        "size": 24,
        "zoom_from": 40,
        "zoom_to": 0,
        "value_a": 2,
        "repr": "lat:120.80° x lon:120.80°",
        "repr_alm": "0386d4 01",
        "is_empty": False,
    },
}


@pytest.fixture(
    scope="function",
    params=list(SCALE_DICT),
    ids=[SCALE_DICT[k]["name"] for k in SCALE_DICT])
def sc_fixture(request):
    """
    Фикстура, которая инициализирует реальный блок 0x08 данными из словаря.
    Вместо чтения бинарного файла, мы наполняем его свойствами.
    """
    scale_from_dict = request.param
    metrics = SCALE_DICT[scale_from_dict]

    # Загружаем экземпляр vdo
    if metrics["dbrev"] == 34:
        if metrics["segsize"] == 0x200:
            path = FIXTURES_DIR / 'DB34_0h_3A01h.bin'
        else:
            path = FIXTURES_DIR / 'carindb34_0h_6800h.bin'
    else:
        path = FIXTURES_DIR / 'carindb30_0h_9000h.bin'

    # Создаем экземпляр класса SCALE
    vdo = VDO_FILE(path)

    sc: SCALE = SCALE(bytes.fromhex(metrics["bin"]), vdo)
    
    # # Изолируем внешнюю зависимость vdo
    # sc.vdo = MagicMock()
    # sc.vdo.dbrev = metrics["dbrev"]
    # sc.vdo.segsize = metrics["segsize"]
    
    return sc, metrics


def test_scale_integrated_examples(sc_fixture):
    """
    Пролверка метрик в наборе фикстурес-масштабов
    """
    sc, metrics = sc_fixture

    assert sc.zoom_from == metrics["zoom_from"]       # 0x4B0
    assert sc.zoom_to == metrics["zoom_to"]
    assert sc.value_a == metrics["value_a"]
    assert sc.size == metrics["size"]
    assert metrics["repr"] in repr(sc)
    assert isinstance(sc.almanac_idx, BLADDR)
    assert metrics["repr_alm"] in repr(sc.almanac_idx)
    assert sc.is_empty == metrics["is_empty"]


# ---------- Tests negative on init

def test_scale_init_err_wrong_vdo():
    vdo = VDO_FILE(FIXTURES_DIR / 'carindb30_0h_9000h.bin')
    strbin = SCALE_DICT['ru34_sc10']["bin"]

    with pytest.raises(TypeError, match="buffer must be bytes"):
        SCALE(strbin, vdo)


def test_scale_init_err_dbrev():
    vdo = VDO_FILE(FIXTURES_DIR / 'carindb30_0h_9000h.bin')
    vdo.dbrev = 10
    bin = bytes.fromhex(SCALE_DICT['ru34_sc10']["bin"])

    with pytest.raises(ValueError, match="dbrev must be 30 or 34"):
        SCALE(bin, vdo)


def test_scale_init_err_too_small_buffer():
    vdo = VDO_FILE()

    with pytest.raises(ValueError, match='Len buffer'):
        SCALE(b'\x00\x01' * 3, vdo)


# -------------- Набор тестов для find_by_coord


@pytest.fixture
def sc_bmw():
    vdo_bmw = VDO_FILE(FIXTURES_DIR / 'DB34_0h_3A01h.bin')
    sc = SCALE(bytes.fromhex(SCALE_DICT["bmw34_sc07"]["bin"]), vdo_bmw)

    return sc


@pytest.mark.parametrize("bin_lon_lat, expected_in_bounds", [
    ("13F919BE13DA074C", True),   # Строго внутри     "59.950064N 30.316605E"
    ("1CA8E32908CB0820", False),   # Строго внутри НО якобы 00 * 28   Ормуз 26.554258N 56.549469E
    ('F76D9000BC7A5000', True),   # На левой нижней границе (включая)   203.910324S 55.886645W
    ('F76D900013DA074C', True),   # На левой границе
    ('13F919BEBC7A5000', True),   # На нижней границе
    ('13F919BE1C7A5000', False),  # На верхней границе (исключая lat >= rt.lat)
    ('576D900013DA074C', False),  # На правой границе (исключая lon >= rt.lon)
    ('576D90001C7A5000', False),  # На правой верхней точке 86.000050N 234.023728E
    ('F76D9010BC7A4010', False),  # Снаружи снизу
    ('576D90101C7A4000', False),  # Снаружи справа
])
def test_scale_coordinate_boundaries(sc_bmw, bin_lon_lat, expected_in_bounds, monkeypatch):
    """Проверяет корректность попадания точки в прямоугольник (включая/исключая границы)."""

    # 1. ЗАБИРАЕМ ДАННЫЕ из реального объекта, пока vdo еще является VDO_FILE
    lb, rt = sc_bmw.area
    if bin_lon_lat == '1CA8E32908CB0820':
        current_almanac_idx = None  # для Ормуза типа scale 00 * 28
    else:
        current_almanac_idx = sc_bmw.almanac_idx  # Успешно создаем валидный BLADDR
    srch_point = COORD(bytes.fromhex(bin_lon_lat))

    # 2. Создаем моки для vdo и возвращаемого им блока альманаха
    mock_vdo = MagicMock()
    mock_alm = MagicMock()
    
    # Настраиваем финальный ответ от вложенного поиска в альманахе
    mock_alm.find_by_coord.return_value = "found_idx"
    # Настраиваем vdo.get_block так, чтобы он возвращал наш мок альманаха
    mock_vdo.get_block.return_value = mock_alm

    # 3. ПОДМЕНЯЕМ vdo НА УРОВНЕ КЛАССА для теста бизнес-логики
    monkeypatch.setattr(type(sc_bmw), "vdo", mock_vdo)

    # 4. ЗАПАТЧИВАЕМ свойство almanac_idx, чтобы оно возвращало уже готовый сохраненный индекс
    # Это предотвратит повторное вычисление и вызов конструктора BLADDR внутри метода
    monkeypatch.setattr(type(sc_bmw), "almanac_idx", current_almanac_idx)

    # 5. Вызов тестируемого метода
    result = sc_bmw.find_by_coord(srch_point)

    # 6. Проверка результатов и вызовов моков
    if expected_in_bounds:
        assert result == "found_idx"
        # Проверяем, что vdo.get_block был вызван с реальным индексом и границами
        mock_vdo.get_block.assert_called_once_with(current_almanac_idx, lb, rt)
        # Проверяем, что поиск внутри альманаха был вызван для нашей точки
        mock_alm.find_by_coord.assert_called_once_with(srch_point)
    else:
        assert result is None
        # Если точка снаружи, запросов к vdo и альманаху быть не должно
        mock_vdo.get_block.assert_not_called()
        mock_alm.find_by_coord.assert_not_called()
