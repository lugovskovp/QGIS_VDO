"""
Функции отображения на карте qgis
"""


from qgis.core import (Qgis, QgsVectorLayer, QgsPointXY, QgsRectangle,
                       QgsSingleSymbolRenderer, QgsFillSymbol, QgsFeature,
                       QgsFeatureRequest, QgsGeometry)
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtCore import Qt

from QGIS_VDO.vdo.consts import (NAME_LAYER_GLOBAL_BOUNDS, NAME_LAYER_ALMANACS)


def _DrawArea(area, area_name: str, layer: QgsVectorLayer) -> None:
    """
    Рисует прямоугольник в слое layer, в котором должен быть атрибут name.
    Args:
        area (coord lb, coord rt)
        area_name: str имя добавляемой area
        layer: QgsVectorLayer Qgis.GeometryType.Polygon:
    """
    field_name_index = layer.fields().indexOf('name')
    # если в слое нет атрибута name - возврат
    if field_name_index == -1:
        return
    # если слой не poligone - возврат
    if not layer or layer.geometryType() != Qgis.GeometryType.Polygon:
        # print("Ошибка: Пожалуйста, выберите ПОЛИГОНАЛЬНЫЙ слой для прямоугольника!")
        return
    # если есть объект с таким именем - возврат
    # Формируем выражение и получаем ID всех подходящих объектов - быстрее перебора
    expression = f"\"name\" = '{area_name}'"
    matching_features = layer.getFeatures(QgsFeatureRequest().setFilterExpression(expression))  # noqa
    ids = [f.id() for f in matching_features]
    if ids:
        return
        # matching_features = layer.getFeatures(QgsFeatureRequest().setFilterExpression(expression))  # noqa
        # ids = [f.id() for f in matching_features]

    # Перебираем все объекты слоя
    # for feature in layer.getFeatures():
    #     # feature.id() — уникальный внутренний номер объекта в QGIS
    #     # feature.attributes() — список всех текстовых/числовых значений в таблице
    #     kk = feature.attributes()
    #     if feature.attribute('name') == area_name:
    #         return
        # print(f"ID: {feature.id()} | {feature.attribute('name')} | Данные: {feature.attributes()}")  # noqa

    # координаты точек
    p_lb = QgsPointXY(area[0].lon, area[0].lat)
    p_rt = QgsPointXY(area[1].lon, area[1].lat)

    # Создаем геометрию прямоугольника
    rect = QgsRectangle(p_lb, p_rt)
    geom = QgsGeometry.fromRect(rect)
    
    # Создаем новый объект (Feature) и присваиваем ему геометрию
    feature = QgsFeature(layer.fields())
    feature.setGeometry(geom)
    
    # Если в слое есть атрибуты, можно задать дефолтные значения (опционально)
    feature.setAttribute(field_name_index, area_name)
   
    # Начинаем редактирование слоя и добавляем объект
    layer.startEditing()
    success = layer.addFeature(feature)

    if success:
        layer.commitChanges()    # Сохраняем изменения
        layer.triggerRepaint()   # Обновляем карту
        # print("Прямоугольник успешно добавлен на слой!")
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
        # renderer для слоя глобальных границ - лесной зелёный
        # Настраиваем стиль (Символогию) Создаем дефолтный символ для полигона
        symbol = QgsFillSymbol.createSimple({'name': 'square'})
        
        # НАСТРОЙКА ЦВЕТА ЗАЛИВКИ (RGBA: Красный, Зеленый, Синий, Альфа/Прозрачность от 0 до 255) # noqa
        # 128 в конце означает 50% прозрачности (0 - полностью прозрачный, 255 - сплошной)  # noqa
        fill_color = QColor(34, 139, 34, 10)   # Лесной зеленый с 10% прозрачностью
        symbol.setColor(fill_color)
        
        # НАСТРОЙКА ГРАНИЦЫ
        symbol.symbolLayer(0).setStrokeColor(QColor(0, 40, 0, 255))  # Черный цвет границы (сплошной) # noqa
        symbol.symbolLayer(0).setStrokeWidth(0.6)                   # Толщина границы в миллиметрах  # noqa
        # Доступные стили границы: Qt.SolidLine, Qt.DashLine, Qt.DotLine и т.д.
        
        # НАСТРОЙКА ОБЩЕЙ ПРОЗРАЧНОСТИ СЛОЯ (Альтернативный вариант от 0.0 до 1.0)
        # symbol.setOpacity(0.7) # 70% непрозрачности для всего символа целиком

    elif layerName == NAME_LAYER_ALMANACS:
        # слой альманах карт - персиковый
        # Настраиваем стиль (Символогию) Создаем дефолтный символ для полигона
        symbol = QgsFillSymbol.createSimple({'name': 'square'})
        # НАСТРОЙКА ЦВЕТА ЗАЛИВКИ (RGBA: Красный, Зеленый, Синий, Альфа/Прозрачность от 0 до 255) # noqa
        fill_color = QColor(255, 229, 180, 10)   # Персиковый с 10% прозрачностью
        symbol.setColor(fill_color)
        # НАСТРОЙКА ГРАНИЦЫ
        symbol.symbolLayer(0).setStrokeColor(QColor(255, 129, 80, 255))  # Персиковый цвет границы (сплошной) # noqa
        symbol.symbolLayer(0).setStrokeWidth(0.6)                   # Толщина границы в миллиметрах  # noqa
        # Доступные стили границы: Qt.SolidLine, Qt.DashLine, Qt.DotLine и т.д.
        symbol.symbolLayer(0).setStrokeStyle(Qt.DashLine)

    else:
        raise ValueError(layerName, "неизвестный слой, _getRendererByName")

    # Применяем настроенный символ к рендереру слоя
    renderer = QgsSingleSymbolRenderer(symbol)
    return renderer
