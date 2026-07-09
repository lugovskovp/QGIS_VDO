"""
Функции отображения на карте qgis
"""


# from qgis.core import (Qgis, QgsProject, QgsVectorLayer, QgsField,
#                        QgsSingleSymbolRenderer, QgsFillSymbol,
#                        QgsPointXY, QgsRectangle, QgsGeometry, QgsFeature,
#                        QgsLayerTreeGroup, QgsCoordinateTransform)
from qgis.core import (Qgis, QgsVectorLayer,
                       QgsPointXY, QgsRectangle, QgsGeometry, QgsFeature
                       )


def _DrawArea(area, area_name: str, layer: QgsVectorLayer) -> None:
    """
    Рисует прямоугольник в слое layer.
    Args:
        area (coord lb, coord rt)
        area_name: str
        layer: QgsVectorLayer
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
