import pytest   # type: ignore
from QGIS_VDO.vdo.datatypes import VDO_FILE

# Явно импортируем фикстуру, чтобы pytest её увидел
from fixtures import bin_file_path      # noqa


@pytest.fixture(scope="function")
def custom_vdo():
    vdo = VDO_FILE()
    vdo.segsize = 2048
    vdo.dbrev = 34
    vdo.path = "C:/Work/fake_test_file.vdo"
    return vdo


@pytest.fixture(scope="function")
def real_vdo(bin_file_path):                # noqa
    vdo = VDO_FILE(bin_file_path)
        
    return vdo
