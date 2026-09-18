"""
Функции отображения на карте qgis
"""


from qgis.core import (Qgis, QgsVectorLayer, QgsPointXY, QgsRectangle, QgsProject,
                       QgsSingleSymbolRenderer, QgsFillSymbol, QgsLineSymbol, QgsMarkerSymbol, QgsFeature,
                       QgsFeatureRequest, QgsGeometry, QgsApplication,
                       QgsCoordinateReferenceSystem, QgsCategorizedSymbolRenderer,
                       QgsLayerTreeLayer, QgsLayerTreeGroup, QgsField, QgsRendererCategory,
                       QgsVectorSimplifyMethod, QgsTextBufferSettings, QgsTextFormat,
                       QgsPalLayerSettings, QgsRuleBasedLabeling, QgsUnitTypes, QgsSimpleLineSymbolLayer,
                       QgsSimpleFillSymbolLayer)
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor, QFont

from QGIS_VDO.vdo.consts import (NAME_LAYER_ALMANACS,
                                 NAME_LAYER_POI,
                                 NAME_LAYER_SHAPES,
                                 NAME_LAYER_LINES,
                                 CRS_NAME, CRS_PROJECTION_STRING,
                                 LAYERS_PROPERTY,
                                 PEN_STYLES,
                                 FILL_STYLES
                                 )


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


def DrawPacketLines(lines_packet: list, layer: QgsVectorLayer) -> None: # noqa
    """
    Пакетно добавляет полилинии в слой layer.
    Args:
        shapes_packet: [GEO_LINES]
        layer: QgsVectorLayer
    """
    # Базовые проверки слоя
    if not layer or layer.geometryType() != Qgis.GeometryType.Line:
        return

    # Извлекаем уникальные блоки из пакета (исключая None/пустые строки)
    packet_blocks = {item.block for item in lines_packet if getattr(item, 'block', None)}
    if not packet_blocks:
        return

    # Получаем индексы полей безопасным способом (вернет -1, если поля нет)
    fields = layer.fields()
    field_idx_variant = fields.indexOf('variant')
    field_idx_render_order = fields.indexOf('render_order')
    field_idx_name = fields.indexOf('name')
    field_idx_id = fields.indexOf('id')
    field_idx_block = fields.indexOf('block')
    # field_idx_coord = fields.indexOf('coord')

    # Оптимизированный сбор существующих блоков в слое
    if field_idx_block != -1:
        # Экранируем одинарные кавычки для SQL
        safe_block_str = ", ".join(f"'{str(block).replace("'", "''")}'" for block in packet_blocks)
        exist_expression = f"\"block\" in ({safe_block_str})"
        
        # Запрашиваем только поле block для максимальной скорости
        request = QgsFeatureRequest().setFilterExpression(exist_expression).setSubsetOfAttributes([field_idx_block])
        existing_blocks = {f.attribute('block') for f in layer.getFeatures(request)}
    else:
        existing_blocks = set()

    # Подготовка списка новых объектов
    features_to_add = []

    for item in lines_packet:
        # Если полигон с таким block уже есть на слое — пропускаем его
        if item.block in existing_blocks:
            continue

        # Проверка на наличие точек, чтобы избежать IndexError на замыкании
        if not getattr(item, 'vrtx', None) or len(item.vrtx) < 2:
            continue

        points_set = [QgsPointXY(coo.lon, coo.lat) for coo in item.vrtx]

        #  Создаем геометрию полигона
        polygon_geom = QgsGeometry.fromPolylineXY(points_set)

        # Создаем объект QgsFeature
        feature = QgsFeature(fields)
        feature.setGeometry(polygon_geom)

        # Безопасная установка атрибутов (только если поля существуют в слое)
        if field_idx_variant != -1:
            feature.setAttribute(field_idx_variant, item.cat.name)
        if field_idx_name != -1:
            feature.setAttribute(field_idx_name, item.name.capitalize() if item.name else "")
        if field_idx_id != -1:
            feature.setAttribute(field_idx_id, item.id)
        if field_idx_block != -1:
            feature.setAttribute(field_idx_block, item.block)
        if field_idx_block != -1:
            feature.setAttribute(field_idx_block, item.block)
        if field_idx_render_order != -1:
            feature.setAttribute(field_idx_render_order, str(item.cat.value))
        
        features_to_add.append(feature)

    # Если добавлять нечего — выходим
    if not features_to_add:
        return

    # Единая транзакция для всего пакета объектов
    was_editable = layer.isEditable()
    if not was_editable:
        if not layer.startEditing():
            print("Не удалось перевести слой в режим редактирования.")
            return
        
    layer.blockSignals(True)
    success = False
    try:
        success = layer.addFeatures(features_to_add)
    except Exception as e:
        print(f"Ошибка при вызове addFeatures: {e}")
    finally:
        layer.blockSignals(False)

    # Фиксация изменений
    if success:
        if not was_editable:
            layer.commitChanges()  # Сохраняем, только если сами открывали транзакцию
        layer.triggerRepaint()
    else:
        if not was_editable:
            layer.rollBack()
        print(f"Не удалось импортировать пакет из {len(features_to_add)} объектов.")

    pass



def DrawPacketShapes(shapes_packet: list, layer: QgsVectorLayer) -> None:   # noqa
    """
    Пакетно добавляет полигоны в слой layer.
    Args:
        shapes_packet: [GEO_SHAPE]
        layer: QgsVectorLayer
    """
    # Базовые проверки слоя
    if not layer or layer.geometryType() != Qgis.GeometryType.Polygon:
        return

    # Извлекаем уникальные блоки из пакета (исключая None/пустые строки)
    packet_blocks = {item.block for item in shapes_packet if getattr(item, 'block', None)}
    if not packet_blocks:
        return

    # Получаем индексы полей безопасным способом (вернет -1, если поля нет)
    fields = layer.fields()
    field_idx_variant = fields.indexOf('variant')
    # field_idx_render_order = fields.indexOf('render_order')
    field_idx_name = fields.indexOf('name')
    field_idx_id = fields.indexOf('id')
    field_idx_block = fields.indexOf('block')
    field_idx_coord = fields.indexOf('coord')

    # Оптимизированный сбор существующих блоков в слое
    if field_idx_block != -1:
        # Экранируем одинарные кавычки для SQL
        safe_block_str = ", ".join(f"'{str(block).replace("'", "''")}'" for block in packet_blocks)
        exist_expression = f"\"block\" in ({safe_block_str})"
        
        # Запрашиваем только поле block для максимальной скорости
        request = QgsFeatureRequest().setFilterExpression(exist_expression).setSubsetOfAttributes([field_idx_block])
        existing_blocks = {f.attribute('block') for f in layer.getFeatures(request)}
    else:
        existing_blocks = set()

    # Подготовка списка новых объектов
    features_to_add = []

    for item in shapes_packet:
        # Если полигон с таким block уже есть на слое — пропускаем его
        if item.block in existing_blocks:
            continue

        # Проверка на наличие точек, чтобы избежать IndexError на замыкании
        if not getattr(item, 'vrtx', None) or len(item.vrtx) < 3:
            continue

        points_set = [QgsPointXY(coo.lon, coo.lat) for coo in item.vrtx]
        #  для замыкания полигона последняя точка должна совпадать с первой
        if points_set[0] != points_set[-1]:
            points_set.append(points_set[0])

        #  Создаем геометрию полигона
        polygon_geom = QgsGeometry.fromPolygonXY([points_set])

        # Создаем объект QgsFeature
        feature = QgsFeature(fields)
        feature.setGeometry(polygon_geom)

        # Безопасная установка атрибутов (только если поля существуют в слое)
        if field_idx_variant != -1:
            feature.setAttribute(field_idx_variant, item.cat.name)
        if field_idx_name != -1:
            feature.setAttribute(field_idx_name, item.name.capitalize() if item.name else "")
        if field_idx_id != -1:
            feature.setAttribute(field_idx_id, item.id)
        if field_idx_block != -1:
            feature.setAttribute(field_idx_block, item.block)
        if field_idx_coord != -1:
            feature.setAttribute(field_idx_coord, str(item.coord))
        
        features_to_add.append(feature)

    # Если добавлять нечего — выходим
    if not features_to_add:
        return

    # Единая транзакция для всего пакета объектов
    was_editable = layer.isEditable()
    if not was_editable:
        if not layer.startEditing():
            print("Не удалось перевести слой в режим редактирования.")
            return
        
    layer.blockSignals(True)
    success = False
    try:
        success = layer.addFeatures(features_to_add)
    except Exception as e:
        print(f"Ошибка при вызове addFeatures: {e}")
    finally:
        layer.blockSignals(False)

    # Фиксация изменений
    if success:
        if not was_editable:
            layer.commitChanges()  # Сохраняем, только если сами открывали транзакцию

        # layer.emitDataChanged()    # Сообщаем подсистеме PAL, что данные подписей изменились
        layer.triggerRepaint()
        # from qgis.utils import iface
        # if iface and iface.mapCanvas():
        #     iface.mapCanvas().refreshAllLayers()  # Полностью сбрасывает кэш PAL и геометрий
        # else:
        #     layer.triggerRepaint()
    else:
        if not was_editable:
            layer.rollBack()
        print(f"Не удалось импортировать пакет из {len(features_to_add)} объектов.")

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


def getLayer(parentGroup: QgsLayerTreeGroup, layerName: str) -> QgsVectorLayer:   # noqa too complex
    """
    Возвращает или создаёт QgsVectorLayer.
    Args:
        parentGroup  :QgsLayerTreeGroup: в какой группе искать/создавать слой
        layerName: str имя слоя, константное название
    Returns:
        layer: QgsVectorLayer
    """
    # Поиск layer в указанной группе.
    if layer := _findLayer_in_Group(parentGroup, layerName):
        return layer

    # Поиск наименования слоя в наборе свойств слоёв
    registry = {obj['name']: obj for obj in LAYERS_PROPERTY}
    target = registry.get(layerName)
    if not target:
        raise AttributeError(f"Ошибка, нет варианта имени слоя {layerName}")
        
    # Создаём новый слой в памяти
    geometry = target.get('geometry')
    uri = f"{geometry}?crs={getCrsProjection().authid()}&index=yes"
    layer = QgsVectorLayer(uri, layerName, "memory")
    if not layer.isValid():
        raise ValueError(f"Не удалось инициализировать слой: {layerName}")

    # Добавляем атрибутивные поля
    attrs = []
    # Строгое чтение корректного ключа 'attributes'
    for attribute, t in target.get('attributes', []):
        attrs.append(QgsField(attribute, t))     # QgsField("id", QMetaType.Type.Int)

    if attrs:
        provider = layer.dataProvider()
        provider.addAttributes(attrs)
        layer.updateFields()    # Обновляем поля в слое после их добавления в провайдер

    # Символика
    symbol_class = GEOMETRY_SYMBOLS.get(geometry)
    if not symbol_class:
        raise ValueError(f"Неизвестный тип геометрии: {geometry}")
    
    # Стили и принудительный порядок
    stiles_list = target.get('styles')
    if not stiles_list:
        raise AttributeError("В конфигурации слоя должен быть как минимум один style")
    
    if len(stiles_list) == 1:
        # Один символ на весь слой
        symbol = _create_complex_symbol(geometry, stiles_list[0])
        renderer = QgsSingleSymbolRenderer(symbol)
    else:
        # Категоризированный рендерер
        categories = []
        for index, style_item in enumerate(stiles_list):
            symbol = _create_complex_symbol(geometry, style_item)
            
            # Настройка z-level отрисовки геометрий внутри слоя
            for l_idx in range(symbol.symbolLayerCount()):
                symbol.symbolLayer(l_idx).setRenderingPass(index)
            
            name = style_item.get('name')
            label = name.capitalize() if name else f"Category {index}"
            categories.append(QgsRendererCategory(name, symbol, label))

        renderer = QgsCategorizedSymbolRenderer("variant", categories)
        renderer.setOrderByEnabled(True)    # Включаем сортировку по пассам рендеринга

    layer.setRenderer(renderer)

    # =========================================================================
    # ДИНАМИЧЕСКИЕ ПОДПИСИ НА ОСНОВЕ ПРАВИЛ
    has_labels = any('label_style' in style_item for style_item in stiles_list)

    if has_labels:
        # Создаем корневой контейнер для правил подписей
        root_rule = QgsRuleBasedLabeling.Rule(QgsPalLayerSettings())

        for style_item in stiles_list:
            label_config = style_item.get('label_style')
            if not label_config:
                continue

            name = style_item.get('name')
            
            # Генерируем формат текста из словаря через функцию-фабрику
            text_format = _build_text_format(label_config)

            # Базовые настройки подписи для конкретного правила
            settings = QgsPalLayerSettings()
            settings.setFormat(text_format)
            settings.fieldName = 'name'

            # Специфичное размещение подписей для линий и полигонов
            if 'Line' in geometry:
                settings.placement = QgsPalLayerSettings.Line
            else:
                settings.placement = QgsPalLayerSettings.Horizontal
            
            # Минимальный размер для отображения подписи
            min_size = label_config.get('label_min_size')
            if min_size is not None:
                settings.minFeatureSize = float(min_size)

            # Блок подавления дубликатов подписей (совместим с QGIS 3.44)
            if label_config.get('remove_duplicates'):
                settings.mergeLines = True
                settings.removeDuplicateLabels = True
                
            # Создаем дочернее правило
            rule = QgsRuleBasedLabeling.Rule(settings)
            rule.setActive(True)
            
            rule.setFilterExpression(f"\"variant\" = '{name}'")
            rule.setDescription(f"Labels for {name}")
            
            root_rule.appendChild(rule)

        # Применяем дерево правил к слою
        rules_labeling = QgsRuleBasedLabeling(root_rule)
        layer.setLabeling(rules_labeling)
        layer.setLabelsEnabled(True)

    # Оптимизация отрисовки на больших масштабах
    simplify_method = QgsVectorSimplifyMethod()
    simplify_method.setSimplifyHints(QgsVectorSimplifyMethod.GeometrySimplification)
    simplify_method.setSimplifyAlgorithm(QgsVectorSimplifyMethod.Distance)
    simplify_method.setTolerance(1.5)
    layer.setSimplifyMethod(simplify_method)

    # Регистрируем в проекте без автоматического отображения в корне панели (False)
    QgsProject.instance().addMapLayer(layer, False)
    
    # Исправлено условие: явная проверка на None, чтобы 'place': 0 работал корректно
    place = target.get('place')
    if place is not None:
        parentGroup.insertLayer(int(place), layer)
    else:
        _add_layer_in_right_order(parentGroup, layer, layerName)

    # Сворачиваем дерево стилей/категорий слоя для аккуратности внутри parentGroup
    layer_node = parentGroup.findLayer(layer.id())
    if layer_node:
        layer_node.setExpanded(False)

    return layer


def _add_layer_in_right_order(group: QgsLayerTreeGroup, new_layer: QgsVectorLayer, layer_key: str):
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


def _create_complex_symbol(geometry_type: str, style_item: dict) -> object:
    """
    Фабрика символов. Поддерживает как стандартные QGIS-строки стилей,
    так и кастомные списки подслоев (сложные символы типа RAILWAY или BORDER).
    """
    symbol_class = GEOMETRY_SYMBOLS.get(geometry_type)
    symbol = symbol_class()
    
    # Извлекаем структуру слоев. Если это один слой, заворачиваем в список.
    # Извлекаем конфигурацию слоев напрямую из ключа 'style'
    style_content = style_item.get('style')
    
    if isinstance(style_content, list):
        # Если внутри 'style' уже лежит список подслоев: [ {...}, {...} ]
        layers_config = style_content
    elif isinstance(style_content, dict):
        # Если там один словарь: {...}, заворачиваем его в список для итерации
        layers_config = [style_content]
    else:
        # Защита на случай, если style пустой или не задан
        layers_config = []
    
    for idx, lyr_cfg in enumerate(layers_config):
        if not lyr_cfg:
            continue
            
        if 'Line' in geometry_type:
            sl = QgsSimpleLineSymbolLayer()
            sl.setColor(_hex_rgba_to_qcolor(lyr_cfg.get('color', '#000000')))
            sl.setWidth(float(lyr_cfg.get('width', 0.3)))
            
            # Поддержка кастомного шага пунктира (Custom Dash)
            if 'custom_dash' in lyr_cfg:
                sl.setUseCustomDashPattern(True)
                sl.setPenStyle(Qt.CustomDashLine)
                sl.setCustomDashVector(lyr_cfg['custom_dash'])
                if 'dash_offset' in lyr_cfg:
                    sl.setDashPatternOffset(float(lyr_cfg['dash_offset']))
            else:
                p_style = lyr_cfg.get('pen_style', 'solid')
                sl.setPenStyle(PEN_STYLES.get(p_style, Qt.SolidLine))
                
        elif 'Polygon' in geometry_type:
            sl = QgsSimpleFillSymbolLayer()
            sl.setFillColor(_hex_rgba_to_qcolor(lyr_cfg.get('fill_color', '#ffffff')))
            sl.setStrokeColor(_hex_rgba_to_qcolor(lyr_cfg.get('outline_color', '#000000')))
            sl.setStrokeWidth(float(lyr_cfg.get('outline_width', 0.2)))
            
            # Конвертация стиля обводки полигона
            p_style = lyr_cfg.get('outline_style', 'solid')
            sl.setStrokeStyle(PEN_STYLES.get(p_style, Qt.SolidLine))
            
            # Конвертация стиля заливки полигона
            f_style = lyr_cfg.get('fill_style', 'solid')
            sl.setBrushStyle(FILL_STYLES.get(f_style, Qt.SolidPattern))

        # Собираем многослойный пирог
        if idx == 0:
            symbol.changeSymbolLayer(0, sl)
        else:
            symbol.appendSymbolLayer(sl)
            
    return symbol


def _hex_rgba_to_qcolor(hex_str):
    # Удаляем решётку, если она есть
    hex_clean = hex_str.lstrip('#')
    
    if len(hex_clean) == 8:
        # Переносим последние 2 символа (AA) в начало -> AARRGGBB
        hex_arrgbb = hex_clean[6:] + hex_clean[:6]
        return QColor(f"#{hex_arrgbb}")
    
    # Если строка без прозрачности (6 символов), возвращаем как есть
    return QColor(hex_str)


def _build_text_format(style_dict: dict) -> QgsTextFormat:
    """Вспомогательная функция для сборки QgsTextFormat из чистого Python dict."""
    fmt = QgsTextFormat()
    if not style_dict:
        return fmt

    # Базовые настройки шрифта
    family = style_dict.get('font_family', 'Arial')
    size = style_dict.get('font_size', 10)
    font = QFont(family, int(size))
    
    if style_dict.get('bold'):
        font.setBold(True)
    if style_dict.get('italic'):
        font.setItalic(True)
    
    fmt.setFont(font)
    fmt.setSize(size)
    # Если в словаре указано, что нужны метры, меняем единицы:
    if style_dict.get('size_in_meters'):
        fmt.setSizeUnit(QgsUnitTypes.RenderMetersInMapUnits)

    # Цвет текста
    fmt.setColor(_hex_rgba_to_qcolor(style_dict.get('color', '#000000')))

    # Настройки буфера (обводка вокруг букв) для читаемости
    if style_dict.get('buffer_enabled'):
        buf = QgsTextBufferSettings()
        buf.setEnabled(True)
        buf.setSize(style_dict.get('buffer_size', 1.0))
        buf.setColor(_hex_rgba_to_qcolor(style_dict.get('buffer_color', 'white')))
        fmt.setBuffer(buf)

    return fmt


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
