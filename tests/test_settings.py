import pytest    # type: ignore # noqa
from qgis.PyQt.QtCore import QSettings, Qt
from QGIS_VDO.settings import Settings
from QGIS_VDO.vdo.consts import DEFAULT_SCALE


@pytest.fixture(autouse=True)
def clean_settings():
    """Фикстура для изоляции тестов. Очищает ветку настроек плагина до и после теста."""
    settings = QSettings()
    settings.beginGroup(Settings.PREFIX)
    settings.remove("")  # Удаляет все ключи в текущей группе
    settings.endGroup()
    yield
    settings.beginGroup(Settings.PREFIX)
    settings.remove("")
    settings.endGroup()


def test_recent_files_count():
    # Проверяем дефолтное значение
    assert Settings.RecentFilesCount() == Settings.DEFAULT_RECENT_FILES_COUNT
    
    # Проверяем запись и чтение
    Settings.setRecentFilesCount(10)
    assert Settings.RecentFilesCount() == 10


def test_last_file_name_path():
    # Дефолтное значение должно быть пустой строкой
    assert Settings.LastFileNamePath() == ''
    
    # Проверяем сохранение пути
    test_path = "/path/to/carindb.db"
    Settings.setLastFileNamePath(test_path)
    assert Settings.LastFileNamePath() == test_path


def test_choused_scale():
    # Дефолтное значение
    assert Settings.ChousedScale() == DEFAULT_SCALE
    
    # Изменение значения
    Settings.setChousedScale(8)
    assert Settings.ChousedScale() == 8


@pytest.mark.slow
def test_recent_files_management():
    # Изначально список должен быть пустым
    assert Settings.RecentFiles() == []

    # Добавляем файлы и проверяем сортировку (новый всегда первый)
    Settings.updateRecentFiles("file1.db")
    Settings.updateRecentFiles("file2.db")
    assert Settings.RecentFiles() == ["file2.db", "file1.db"]

    # Проверяем перемещение существующего файла в начало списка
    Settings.updateRecentFiles("file1.db")
    assert Settings.RecentFiles() == ["file1.db", "file2.db"]

    # Проверяем ограничение по RecentFilesCount (по умолчанию 5)
    for i in range(10):
        Settings.updateRecentFiles(f"file_{i}.db")

    # С ListAll=False возвращает только обрезанный список
    assert len(Settings.RecentFiles(ListAll=False)) == Settings.DEFAULT_RECENT_FILES_COUNT
    # С ListAll=True возвращает все сохраненные файлы
    assert len(Settings.RecentFiles(ListAll=True)) == 12    # 'file_1.db', 'file_0.db', 'file1.db', 'file2.db'

    # Проверяем жесткое ограничение MAX_RECENT_FILES_COUNT
    for i in range(30):
        Settings.updateRecentFiles(f"many_{i}.db")
    assert len(Settings.RecentFiles(ListAll=True)) == Settings.MAX_RECENT_FILES_COUNT

    # Удаление одного файла
    Settings.removeRecentFiles("many_29.db")
    assert "many_29.db" not in Settings.RecentFiles(ListAll=True)

    # Полная очистка
    Settings.clearRecentFiles()
    assert Settings.RecentFiles(ListAll=True) == []


def test_tool_button_style():
    # По умолчанию текст включен
    assert Settings.toolButtonTextEnabled() is True
    assert Settings.toolButtonStyle() == Qt.ToolButtonStyle.ToolButtonTextBesideIcon

    # Отключаем текст
    Settings.setToolButtonTextEnabled(False)
    assert Settings.toolButtonTextEnabled() is False
    assert Settings.toolButtonStyle() == Qt.ToolButtonStyle.ToolButtonIconOnly


def test_show_clear_recent_files_enabled():
    assert Settings.ShowClearRecentFilesEnabled() is False
    Settings.setShowClearRecentFilesEnabled(True)
    assert Settings.ShowClearRecentFilesEnabled() is True


def test_hide_non_active_vdo_enabled():
    # Внимание: в вашем коде метода HideNonActiveVdoEnabled используется NAME_ENABLE_SHOW_CLEAR_ACTION
    assert Settings.HideNonActiveVdoEnabled() is False
    Settings.setHideNonActiveVdo(True)
    assert Settings.HideNonActiveVdoEnabled() is True


def test_show_group_box_enabled():
    group_name = "tab_info_group"
    # По умолчанию True
    assert Settings.ShowGroupBoxEnabled(group_name) is True
    
    # Меняем состояние
    Settings.setShowGroupBoxEnabled(group_name, False)
    assert Settings.ShowGroupBoxEnabled(group_name) is False
    
    # Другая группа должна остаться True
    assert Settings.ShowGroupBoxEnabled("other_group") is True
