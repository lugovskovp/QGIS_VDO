import pytest   # type: ignore
from QGIS_VDO.vdo.datatypes import VDO_FILE


@pytest.fixture(scope="function")
def custom_vdo():
    """
    Фикстура, создающая изолированный тестовый контекст VDO_FILE.
    Автоматически подставляется в любой тест, где есть аргумент 'custom_vdo'.
    """
    # Инициализируем пустой объект (вызовется метод .empty() без чтения с диска)
    vdo = VDO_FILE()
    
    # Жестко задаем тестовые параметры
    vdo.segsize = 2048
    vdo.dbrev = 34
    vdo.path = "C:/Work/fake_test_file.vdo"
    
    return vdo
