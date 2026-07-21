"""
Функции отображения на карте qgis
"""


# from qgis.core import (Qgis, QgsProject, QgsVectorLayer, QgsField,
#                        QgsSingleSymbolRenderer, QgsFillSymbol,
#                        QgsPointXY, QgsRectangle, QgsGeometry, QgsFeature,
#                        QgsLayerTreeGroup, QgsCoordinateTransform)
from qgis.core import (Qgis, QgsVectorLayer, QgsPointXY, QgsRectangle,
                       QgsSingleSymbolRenderer, QgsFillSymbol, QgsFeature,
                       QgsGeometry)
from qgis.PyQt.QtGui import QColor

from QGIS_VDO.vdo.consts import NAME_LAYER_GLOBAL_BOUNDS, NAME_LAYER_ALMANACS


def _DrawArea(area, area_name: str, layer: QgsVectorLayer) -> None:
    """
    Рисует прямоугольник в слое layer.
    Args:
        area (coord lb, coord rt)
        area_name: str
        layer: QgsVectorLayer Qgis.GeometryType.Polygon:
    """
    # если есть объект с таким именем - возврат
    # Перебираем все объекты слоя
    for feature in layer.getFeatures():
        # feature.id() — уникальный внутренний номер объекта в QGIS
        # feature.attributes() — список всех текстовых/числовых значений в таблице
        if feature.attribute('name') == area_name:
            return
        print(f"ID: {feature.id()} | {feature.attribute('name')} | Данные: {feature.attributes()}")  # noqa

    # если слой не poligone - возврат
    if not layer or layer.geometryType() != Qgis.GeometryType.Polygon:
        print("Ошибка: Пожалуйста, выберите ПОЛИГОНАЛЬНЫЙ слой для прямоугольника!")
        return

    # координаты точек
    p_lb = QgsPointXY(area[0].lon, area[0].lat)
    p_rt = QgsPointXY(area[1].lon, area[1].lat)

    # Создаем геометрию прямоугольника
    rect = QgsRectangle(p_lb, p_rt)
    geom = QgsGeometry.fromRect(rect)
    
    # Создаем новый объект (Feature) и присваиваем ему геометрию
    feature = QgsFeature()
    feature.setGeometry(geom)
    
    # Если в слое есть атрибуты, можно задать дефолтные значения (опционально)
    feature.setAttributes([1, area_name, f"{area[0].__repr__()}, {area[1].__repr__()}"])  # noqa

    # Начинаем редактирование слоя и добавляем объект
    layer.startEditing()
    success = layer.addFeature(feature)

    if success:
        layer.commitChanges()    # Сохраняем изменения
        layer.triggerRepaint()   # Обновляем карту
        print("Прямоугольник успешно добавлен на слой!")
    else:
        layer.rollBack()     # Отменяем правки в случае ошибки
        print("Не удалось добавить объект на слой.")

    pass


def getRendererByLayerName(layerName: str) -> QgsSingleSymbolRenderer:
    """
    свойства отображения слоя по наименованию слоя
    фактически просто вынесенные отдельно библиотека
    """
    #
    if layerName == NAME_LAYER_GLOBAL_BOUNDS:
        # renderer для слоя глобальных границ
        # Настраиваем стиль (Символогию) Создаем дефолтный символ для полигона
        symbol = QgsFillSymbol.createSimple({'name': 'square'})
        
        # НАСТРОЙКА ЦВЕТА ЗАЛИВКИ (RGBA: Красный, Зеленый, Синий, Альфа/Прозрачность от 0 до 255) # noqa
        # 128 в конце означает 50% прозрачности (0 - полностью прозрачный, 255 - сплошной)  # noqa
        fill_color = QColor(34, 139, 34, 20)   # Лесной зеленый с 20% прозрачностью
        symbol.setColor(fill_color)
        
        # НАСТРОЙКА ГРАНИЦЫ
        symbol.symbolLayer(0).setStrokeColor(QColor(0, 0, 0, 255))  # Черный цвет границы (сплошной) # noqa
        symbol.symbolLayer(0).setStrokeWidth(0.6)                   # Толщина границы в миллиметрах  # noqa
        # Доступные стили границы: Qt.SolidLine, Qt.DashLine, Qt.DotLine и т.д.
        
        # НАСТРОЙКА ОБЩЕЙ ПРОЗРАЧНОСТИ СЛОЯ (Альтернативный вариант от 0.0 до 1.0)
        # symbol.setOpacity(0.7) # 70% непрозрачности для всего символа целиком
    elif layerName == NAME_LAYER_ALMANACS:
        # слой альманах карт
        symbol = 0
    else:
        raise ValueError(layerName, "неизвестно, _getRendererByName")

    # Применяем настроенный символ к рендереру слоя
    renderer = QgsSingleSymbolRenderer(symbol)
    return renderer
