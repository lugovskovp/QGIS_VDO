"""
Функции отображения на карте qgis
"""


from qgis.core import (Qgis, QgsVectorLayer, QgsPointXY, QgsRectangle,
                       QgsSingleSymbolRenderer, QgsFillSymbol, QgsFeature,
                       QgsFeatureRequest, QgsGeometry)
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtCore import Qt

from QGIS_VDO.vdo.consts import (NAME_LAYER_GLOBAL_BOUNDS,
                                 NAME_LAYER_ALMANACS,
                                 NAME_LAYER_MAPS)


def _DrawArea(area, area_name: str, layer: QgsVectorLayer) -> None:
    """
    Рисует прямоугольник в слое layer, в котором должен быть атрибут name.
    Args:
        area: aaraay of tylpes val coordf
            [(lon, lat), (lon, lat)]
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
    # TODO: временно
    (la, lo) = area[0]
    if la > 85:
        la = 85
    if la < -85:
        la = -85
    p_lb = QgsPointXY(lo, la)       # (X, Y) -> (Долгота (Long) E/W, Широта (Lat) N/S)
    (la, lo) = area[1]
    if la > 85:
        la = 85
    if la < -85:
        la = -85
    p_rt = QgsPointXY(lo, la)

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


def _DrawPacketAreas(areas_packet: list, layer: QgsVectorLayer) -> None:
    """
    Пакетно добавляет прямоугольники в слой layer.
    
    Args:
        areas_packet: список словарей или кортежей с данными объектов.
                      Пример формата: [ {"area": [(lat, lon), (lat, lon)], "name": "Имя1"}, ... ]  # noqa
        layer: Целевой полигональный слой QgsVectorLayer
    """
    # Базовые проверки слоя
    if not layer or layer.geometryType() != Qgis.GeometryType.Polygon:
        return

    field_name_index = layer.fields().indexOf('name')
    if field_name_index == -1:
        print("Ошибка: В слое отсутствует обязательное поле 'name'")
        return

    # Оптимизированный сбор существующих имен в слое (чтобы избежать дубликатов)
    # Собираем уникальные имена из пришедшего пакета, чтобы отфильтровать их одним запросом  # noqa
    packet_names = {item["name"] for item in areas_packet if "name" in item}
    if not packet_names:
        return

    # Формируем SQL-выражение для поиска существующих имен: "name" IN ('Имя1', 'Имя2')
    safe_names_str = ", ".join(f"'{name.replace("'", "''")}'" for name in packet_names)
    exist_expression = f"\"name\" IN ({safe_names_str})"
    
    request = QgsFeatureRequest().setFilterExpression(exist_expression).setSubsetOfAttributes([field_name_index])  # noqa
    existing_names = {f.attribute('name') for f in layer.getFeatures(request)}

    # 3. Подготовка списка новых объектов
    features_to_add = []

    for item in areas_packet:
        area = item.get("area")
        area_name = item.get("name")

        if not area or not area_name:
            continue

        # Если полигон с таким именем уже есть на слое — пропускаем его
        if area_name in existing_names:
            continue

        # Извлекаем и валидируем широту/долготу
        lat1, lon1 = area[0]
        lat2, lon2 = area[1]

        # Защита от выхода за границы стандартных проекций (Web Mercator)
        lat1 = max(-85.0, min(85.0, lat1))
        lat2 = max(-85.0, min(85.0, lat2))

        # Геометрия требует правильного порядка углов (XMin, YMin, XMax, YMax)
        x_min, x_max = min(lon1, lon2), max(lon1, lon2)
        y_min, y_max = min(lat1, lat2), max(lat1, lat2)

        rect = QgsRectangle(x_min, y_min, x_max, y_max)
        geom = QgsGeometry.fromRect(rect)
        
        # Создаем объект QgsFeature
        feature = QgsFeature(layer.fields())
        feature.setGeometry(geom)
        feature.setAttribute(field_name_index, area_name)
        
        features_to_add.append(feature)

    # Если добавлять нечего — выходим
    if not features_to_add:
        return

    # Единая транзакция для всего пакета объектов
    was_editable = layer.isEditable()
    if not was_editable:
        layer.startEditing()
        
    # Блокируем сигналы изменения слоя на время массовой вставки (прирост скорости)
    layer.blockSignals(True)
    try:
        # addFeatures принимает list и работает в разы быстрее, чем addFeature в цикле
        success = layer.addFeatures(features_to_add)
    finally:
        layer.blockSignals(False)

    # Фиксация изменений
    if success:
        if not was_editable:
            layer.commitChanges()  # Сохраняем на диск/в память один раз за пакет
        layer.triggerRepaint()     # Перерисовываем карту один раз за пакет
    else:
        if not was_editable:
            layer.rollBack()
        print(f"Не удалось импортировать пакет из {len(features_to_add)} объектов.")


def getRendererByLayerName(layerName: str) -> QgsSingleSymbolRenderer:
    """
    свойства отображения слоя по наименованию слоя
    фактически просто вынесенные отдельно библиотекой
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
        symbol.symbolLayer(0).setStrokeWidth(0.2)                   # Толщина границы в миллиметрах  # noqa
        # Доступные стили границы: Qt.SolidLine, Qt.DashLine, Qt.DotLine и т.д.
        symbol.symbolLayer(0).setStrokeStyle(Qt.DashLine)

    elif layerName == NAME_LAYER_MAPS:
        # слой карт - желтый
        # Настраиваем стиль (Символогию) Создаем дефолтный символ для полигона
        symbol = QgsFillSymbol.createSimple({'name': 'square'})
        # НАСТРОЙКА ЦВЕТА ЗАЛИВКИ (RGBA: Красный, Зеленый, Синий, Альфа/Прозрачность от 0 до 255) # noqa
        fill_color = QColor(255, 229, 180, 80)   # Персиковый с 10% прозрачностью
        symbol.setColor(fill_color)
        # НАСТРОЙКА ГРАНИЦЫ
        symbol.symbolLayer(0).setStrokeColor(QColor(255, 229, 0, 255))  # Персиковый цвет границы (сплошной) # noqa
        symbol.symbolLayer(0).setStrokeWidth(0.4)                   # Толщина границы в миллиметрах  # noqa
        # Доступные стили границы: Qt.SolidLine, Qt.DashLine, Qt.DotLine и т.д.
        symbol.symbolLayer(0).setStrokeStyle(Qt.DotLine)

    else:
        raise ValueError(layerName, "неизвестный слой, _getRendererByName")

    # Применяем настроенный символ к рендереру слоя
    renderer = QgsSingleSymbolRenderer(symbol)
    return renderer
