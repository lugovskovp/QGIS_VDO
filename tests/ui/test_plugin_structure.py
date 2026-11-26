"""Тесты структуры плагина — проверка обязательных методов и классов."""

from unittest.mock import MagicMock, patch

import pytest       # noqa


def test_classFactory_exists():
    """Функция classFactory существует в __init__."""
    from QGIS_VDO import classFactory
    assert callable(classFactory)


def test_classFactory_returns_plugin():
    """classFactory возвращает экземпляр плагина."""
    from QGIS_VDO import classFactory

    mock_iface = MagicMock()
    # QSettings().value() возвращает None в headless-режиме
    with patch('qgis.PyQt.QtCore.QSettings') as mock_qs:
        instance = MagicMock()
        instance.value.return_value = 'en_US'
        mock_qs.return_value = instance

        plugin = classFactory(mock_iface)

    assert plugin is not None
    # classFactory создаёт VDOExplorerPlugin
    from QGIS_VDO.vdo_explorer import VDOExplorerPlugin
    assert isinstance(plugin, VDOExplorerPlugin)


def test_plugin_class_has_required_methods():
    """Класс плагина имеет обязательные методы QGIS API."""
    from QGIS_VDO.vdo_explorer import VDOExplorerPlugin

    assert hasattr(VDOExplorerPlugin, 'initGui')
    assert hasattr(VDOExplorerPlugin, 'unload')
    assert callable(VDOExplorerPlugin.initGui)
    assert callable(VDOExplorerPlugin.unload)


def test_initGui_with_mock_iface():
    """initGui не бросает исключение с mock-iface."""
    from QGIS_VDO.vdo_explorer import VDOExplorerPlugin

    mock_iface = MagicMock()
    mock_iface.addPluginToWebMenu = MagicMock()
    mock_iface.addToolBarIcon = MagicMock()
    mock_iface.mainWindow = MagicMock()

    # QSettings().value() возвращает None в headless-режиме
    with patch('qgis.PyQt.QtCore.QSettings') as mock_qs:
        qs_instance = MagicMock()
        qs_instance.value.return_value = 'en_US'
        mock_qs.return_value = qs_instance

        plugin = VDOExplorerPlugin(mock_iface)
    # Не должно бросить
    plugin.initGui()


def test_unload_is_safe():
    """unload можно вызвать даже без initGui."""
    from QGIS_VDO.vdo_explorer import VDOExplorerPlugin

    mock_iface = MagicMock()

    with patch('qgis.PyQt.QtCore.QSettings') as mock_qs:
        qs_instance = MagicMock()
        qs_instance.value.return_value = 'en_US'
        mock_qs.return_value = qs_instance

        plugin = VDOExplorerPlugin(mock_iface)
    # Не должно бросить
    plugin.unload()


def test_unload_after_initGui():
    """unload корректно работает после initGui."""
    from QGIS_VDO.vdo_explorer import VDOExplorerPlugin

    mock_iface = MagicMock()
    mock_iface.addPluginToWebMenu = MagicMock()
    mock_iface.addToolBarIcon = MagicMock()
    mock_iface.mainWindow = MagicMock()

    with patch('qgis.PyQt.QtCore.QSettings') as mock_qs:
        qs_instance = MagicMock()
        qs_instance.value.return_value = 'en_US'
        mock_qs.return_value = qs_instance

        plugin = VDOExplorerPlugin(mock_iface)

    plugin.initGui()
    plugin.unload()
