"""
Функции отображения на карте qgis
"""


from qgis.core import (Qgis, QgsVectorLayer, QgsPointXY, QgsRectangle, QgsProject,
                       QgsSingleSymbolRenderer, QgsFillSymbol, QgsLineSymbol, QgsMarkerSymbol, QgsFeature,
                       QgsFeatureRequest, QgsGeometry, QgsApplication,
                       QgsCoordinateReferenceSystem, QgsCategorizedSymbolRenderer,
                       QgsLayerTreeLayer, QgsLayerTreeGroup, QgsField, QgsRendererCategory,
                       QgsVectorSimplifyMethod)

from QGIS_VDO.vdo.consts import (NAME_LAYER_ALMANACS,
                                 NAME_LAYER_POI,
                                 NAME_LAYER_SHAPES,
                                 NAME_LAYER_LINES,
                                 CRS_NAME, CRS_PROJECTION_STRING,
                                 LAYERS_PROPERTY)


ORDER_PRIORITY = [NAME_LAYER_POI, NAME_LAYER_LINES, NAME_LAYER_SHAPES, NAME_LAYER_ALMANACS]

GEOMETRY_SYMBOLS = {
    'Polygon': QgsFillSymbol,
    'LineString': QgsLineSymbol,
    'Point': QgsMarkerSymbol
}

 
def _DrawRectangleArea(area, area_name: str, layer: QgsVectorLayer, variant: str | None = None) -> None:
    """
    Рисует прямоугольник в слое layer, в котором должен быть атрибут name.
    Args:
        area: araay of tuples val coord
            [(lon, lat), (lon, lat)]
        area_name: str имя добавляемой area
        variant: отображение, layout или map
        layer: QgsVectorLayer Qgis.GeometryType.Polygon:
    """
    field_name_index = layer.fields().indexOf('name')
    if variant:
        field_variant_index = layer.fields().indexOf('variant')
        if field_variant_index == -1:
            return
    
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
    if variant:
        feature.setAttribute(field_variant_index, variant)
   
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
    field_variant_index = layer.fields().indexOf('variant')
    if field_name_index == -1:
        raise AttributeError("Ошибка: В слое отсутствует обязательное поле 'name'")
        return
    if field_variant_index == -1:
        raise AttributeError("Ошибка: В слое отсутствует обязательное поле 'variant'")

    # Оптимизированный сбор существующих имен в слое (чтобы избежать дубликатов)
    # Собираем уникальные имена из пришедшего пакета, чтобы отфильтровать их одним запросом  # noqa
    packet_names = {item["name"] for item in areas_packet if "name" in item}
    if not packet_names:
        return

    # Формируем SQL-выражение для поиска существующих имен: "name" IN ('Имя1', 'Имя2')
    safe_names_str = ", ".join(f"""'{name.replace("'", "''")}'""" for name in packet_names)
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
        feature.setAttribute(field_variant_index, 'map')
        
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


def _findLayer_in_Group(group: QgsLayerTreeGroup, LayerName: str) -> QgsVectorLayer | None:
    """
    Ищет LayerName в группе group
    Args:
        group:
        LayerName: имя слоя
    """
    # В группе ищем слой
    for child in group.children():
        # Проверяем, что дочерний элемент — это слой и его имя совпадает
        if isinstance(child, QgsLayerTreeLayer) and child.name() == LayerName:
            layer = child.layer()
            # Убеждаемся, что это векторный слой
            if isinstance(layer, QgsVectorLayer):
                return layer
            else:
                raise ValueError(f"Что не так с {layer.name()}")
    return None


def getLayer(parentGroup: QgsLayerTreeGroup, layerName: str) -> QgsVectorLayer:
    """
    Возвращает или создаёт QgsVectorLayer
    Args:
        parentGroup  :QgsLayerTreeGroup: в какой группе
        layerName: str имя слоя, константное название
    Returns:
        layer: QgsVectorLayer
    """
    # Поиск layer в указанной группе.
    if layer := _findLayer_in_Group(parentGroup, layerName):
        return layer

    # поиск наименования слоя в наборе свойств слоёв
    registry = {obj['name']: obj for obj in LAYERS_PROPERTY}
    target = registry.get(layerName)
    if not target:
        raise AttributeError(f"Ошибка, нет варианта имени слоя {layerName}")
        
    # Создаём новый слой.
    geometry = target.get('geometry')
    uri = f"{geometry}?crs={getCrsProjection().authid()}&index=yes"
    layer = QgsVectorLayer(uri, layerName, "memory")

    # Добавляем атрибутивные поля
    attrs = []
    for atribute, t in target.get('atributes'):
        attrs.append(QgsField(atribute, t))     # QgsField("id", QMetaType.Type.Int)
    if len(attrs) > 0:
        provider = layer.dataProvider()
        provider.addAttributes(attrs)
        layer.updateFields()    # Обновляем поля в слое после их добавления в провайдер
    del attrs

    # символика
    symbol_class = GEOMETRY_SYMBOLS.get(geometry)
    if not symbol_class:
        raise ValueError(f"Неизвестный тип геометрии: {geometry}")
    
    # Стили и принудительный порядок (layout всегда поверх map)
    stiles_list = target.get('styles')
    if len(stiles_list) == 0:
        raise AttributeError("Непорядок, хоть один то style должен быть")
    elif len(stiles_list) == 1:
        # если только один символ в слое
        style = stiles_list[0].get('style')
        symbol = symbol_class().createSimple(style)
        renderer = QgsSingleSymbolRenderer(symbol)
    else:
        categories = []
        for index, style_item in enumerate(target.get('styles')):
            style = style_item.get('style')
            symbol = symbol_class().createSimple(style)
            symbol.symbolLayer(0).setRenderingPass(index)       # 0 - Снизу
            name = style_item.get('name')
            categories.append(QgsRendererCategory(name, symbol, name.capitalize()))
        del style, name
        renderer = QgsCategorizedSymbolRenderer("variant", categories)
        renderer.setOrderByEnabled(True)    # Включаем сортировку по пассам рендеринга

    layer.setRenderer(renderer)

    # Оптимизация отрисовки на больших масштабах
    simplify_method = QgsVectorSimplifyMethod()     # объект настроек упрощения
    simplify_method.setSimplifyHints(QgsVectorSimplifyMethod.GeometrySimplification)    # noqa упрощение геометрии при отрисовке
    simplify_method.setSimplifyAlgorithm(QgsVectorSimplifyMethod.Distance)  # noqa алгоритм (Distance — на основе расстояния между узлам
    simplify_method.setTolerance(1.5)   # noqa порог упрощения в пикселях экрана (детали меньше 1.5 пикселей будут сглажены)
    layer.setSimplifyMethod(simplify_method)

    # Проверяем валидность и добавляем слой в нашу верхнюю группу
    if layer.isValid():
        # Регистрируем в проекте без автоматического отображения в панели (False)  # noqa
        QgsProject.instance().addMapLayer(layer, False) # noqa
        place = target.get('place')
        if place:
            # индекс есть в объекте
            parentGroup.insertLayer(int(place), layer)
        else:
            # Вставляем слой на правильное место внутри нашей новой группы
            add_layer_in_right_order(parentGroup, layer, layerName)
        # скрываем по умолчанию категории слоя
        layer_node = QgsProject.instance().layerTreeRoot().findLayer(layer)
        layer_node.setExpanded(False)
        return layer
    else:
        raise ValueError("Не удалось создать новый слой.")


def add_layer_in_right_order(group: QgsLayerTreeGroup, new_layer: QgsVectorLayer, layer_key: str):
    """
    Добавляет слой в QGIS на строго определенную позицию.
    layer_key: 'poi', 'lines', 'shapes' или 'almanac'
    """
    if layer_key not in ORDER_PRIORITY:
        raise ValueError(f"Неизвестный тип слоя: {layer_key}")

    # Вычисляем правильный индекс для вставки
    # Ищем, сколько слоев с БОЛЕЕ ВЫСОКИМ приоритетом уже есть на панели
    target_index = 0
    current_nodes = group.children()    # Все элементы на панели сверху вниз
    
    # Определяем ранг текущего добавляемого слоя (0 для poi, 1 для lines и т.д.)
    new_layer_rank = ORDER_PRIORITY.index(layer_key)
    
    for node in current_nodes:
        # Проверяем только векторные слои
        if hasattr(node, 'layer') and node.layer():
            existing_layer_name = node.layer().name().lower()
            
            # Определяем ранг уже существующего на панели слоя
            existing_rank = None
            for rank, key in enumerate(ORDER_PRIORITY):
                if key in existing_layer_name:    # Проверка на частичное вхождение или точное имя
                    existing_rank = rank
                    break
            
            # Если ранг существующего слоя выше или равен нашему,
            # мы должны пропустить его и встать ПОД ним (увеличиваем индекс вставки)
            if existing_rank is not None and existing_rank <= new_layer_rank:
                target_index += 1
                
    # Вставляем слой на вычисленную позицию
    group.insertLayer(target_index, new_layer)


def getCrsProjection() -> QgsCoordinateReferenceSystem:
    """
    Создаёт, регистрирует и возвращает СК CRS_PROJECTION
    с разрывом на -80w
    CRS_NAME = "WGS 84 / Custom Pacific Split -80"
    CRS_PROJECTION_STRING = "PROJ4:+proj=longlat +lon_0=100 +datum=WGS84 +no_defs"
    """
    # Сначала пытаемся найти СК по имени в реестре пользовательских проекций
    registry = QgsApplication.coordinateReferenceSystemRegistry()
    # Перебираем уже существующие кастомные СК, чтобы не плодить дубликаты
    for user_crs_info in registry.userCrsList():
        if user_crs_info.name == CRS_NAME:
            # Загружаем полноценный объект СК по её внутреннему ID (srsid)
            existing_crs = QgsCoordinateReferenceSystem()
            existing_crs.createFromSrsId(user_crs_info.id)
            return existing_crs
    
    # Если СК не найдена, создаем объект СК на основе строки PROJ
    temp_crs = QgsCoordinateReferenceSystem(CRS_PROJECTION_STRING)
    if not temp_crs.isValid():
        raise Exception(f"Ошибка: Невалидная строка PROJ:'{CRS_PROJECTION_STRING}'. Проверьте параметры проекции.")
    # Сохраняем её в реестр QGIS как новую пользовательскую (USER) СК
    # Метод addUserCrs возвращает назначенный внутренний srsid (например, 100005)
    new_srsid = registry.addUserCrs(temp_crs, CRS_NAME)
    if new_srsid != -1:
        # Инициализируем и возвращаем уже официально зарегистрированную СК
        registered_crs = QgsCoordinateReferenceSystem()
        registered_crs.createFromSrsId(new_srsid)
        return registered_crs
    else:
        raise Exception("Не удалось сохранить пользовательскую СК в базу данных QGIS.")
