"""Тесты для ConfigurationDialog — диалог настроек плагина."""

import sys
import pytest

from qgis.PyQt.QtWidgets import QApplication

from QGIS_VDO.settings import Settings
from QGIS_VDO.ui_files.ConfigurationDialog import ConfigurationDialog


@pytest.fixture(scope="module")
def qapp():
    """Единственный QApplication на модуль."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


def test_dialog_creation(qapp):
    """Диалог настроек создаётся без ошибок."""
    dialog = ConfigurationDialog(parent=None)
    assert dialog is not None
    assert dialog.windowTitle() != ""
    dialog.close()


def test_dialog_widgets_exist(qapp):
    """Все виджеты на месте."""
    dialog = ConfigurationDialog(parent=None)

    assert dialog.cbToolButtonText is not None
    assert dialog.cbShowClearRecent is not None
    assert dialog.cbHideNonActiveVdo is not None
    assert dialog.cbExtraCommands is not None
    assert dialog.pteExtraCommands is not None
    assert dialog.lblExtraCommands is not None
    assert dialog.sbRecentFilesCount is not None
    assert dialog.buttonBox is not None

    dialog.close()


def test_dialog_widgets_enabled(qapp):
    """Виджеты доступны для взаимодействия."""
    dialog = ConfigurationDialog(parent=None)

    assert dialog.cbToolButtonText.isEnabled()
    assert dialog.cbShowClearRecent.isEnabled()
    assert dialog.cbHideNonActiveVdo.isEnabled()
    assert dialog.sbRecentFilesCount.isEnabled()

    # pteExtraCommands и lblExtraCommands отключены по умолчанию
    assert dialog.pteExtraCommands.isEnabled() is False
    assert dialog.lblExtraCommands.isEnabled() is False

    dialog.close()


def test_dialog_extra_commands_toggle(qapp):
    """Включение cbExtraCommands активирует pteExtraCommands и lblExtraCommands."""
    dialog = ConfigurationDialog(parent=None)

    # До включения — отключены
    assert dialog.pteExtraCommands.isEnabled() is False
    assert dialog.lblExtraCommands.isEnabled() is False

    # Включаем
    dialog.cbExtraCommands.setChecked(True)
    assert dialog.pteExtraCommands.isEnabled() is True
    assert dialog.lblExtraCommands.isEnabled() is True

    # Выключаем
    dialog.cbExtraCommands.setChecked(False)
    assert dialog.pteExtraCommands.isEnabled() is False
    assert dialog.lblExtraCommands.isEnabled() is False

    dialog.close()


def test_dialog_spinbox_range(qapp):
    """QSpinBox имеет корректный диапазон."""
    dialog = ConfigurationDialog(parent=None)

    assert dialog.sbRecentFilesCount.minimum() == 1
    assert dialog.sbRecentFilesCount.maximum() == 32

    dialog.close()


def test_dialog_accept(qapp):
    """accept() не бросает исключение."""
    dialog = ConfigurationDialog(parent=None)

    dialog.cbToolButtonText.setChecked(True)
    dialog.sbRecentFilesCount.setValue(20)

    # accept() должен завершиться без ошибок
    dialog.accept()
    dialog.close()


def test_dialog_reject(qapp):
    """reject() не бросает исключение."""
    dialog = ConfigurationDialog(parent=None)

    dialog.cbToolButtonText.setChecked(True)

    # reject() должен завершиться без ошибок
    dialog.reject()
    dialog.close()


def test_dialog_default_values(qapp):
    """Проверка значений по умолчанию — берутся из Settings."""
    dialog = ConfigurationDialog(parent=None)

    # Значение берётся из Settings.RecentFilesCount() (синглтон)
    expected = Settings.RecentFilesCount() or 1
    assert dialog.sbRecentFilesCount.value() == expected

    dialog.close()
