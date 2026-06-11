

# Интегрированный парсер-валидатор ГИС-координат

import binascii
import heapq
import math

def generate_huffman_lookup(weights_table):
    """Строит дерево Хаффмана для однобайтовых токенов (0x00 - 0xFF)."""
    heap = []
    counter = 0
    for key_hex, weight in weights_table.items():
        try:
            char_id = int(key_hex, 16)
            if 0 <= char_id <= 0xFF and weight > 0:
                node = {'id': char_id, 'left': None, 'right': None}
                heapq.heappush(heap, (weight, counter, node))
                counter += 1
        except ValueError:
            continue

    if not heap: return {}
    while len(heap) > 1:
        w1, _, n1 = heapq.heappop(heap)
        w2, _, n2 = heapq.heappop(heap)
        heapq.heappush(heap, (w1 + w2, counter, {'id': None, 'left': n1, 'right': n2}))
        counter += 1

    _, _, root_node = heap[0] # Исправленное извлечение корня из кучи
    huffman_lookup = {}
    
    def walk_tree(node, current_code):
        if node['id'] is not None:
            huffman_lookup[current_code] = node['id']
            return
        if node['left']: walk_tree(node['left'], current_code + "0")
        if node['right']: walk_tree(node['right'], current_code + "1")

    walk_tree(root_node, "")
    return huffman_lookup


def validate_road_smoothness(points):
    """
    Математический анализатор плавности траектории.
    Рассчитывает скор (0-100) и выдает вердикт: дорога или белый шум.
    """
    if len(points) < 3:
        return "КРИТИЧЕСКИ: Слишком мало точек для геометрического анализа."
        
    distances = []
    angles = []
    
    # 1. Вычисляем расстояния (шаги) между точками и вектора смещений
    vectors = []
    for i in range(len(points) - 1):
        dx = points[i+1][0] - points[i][0]
        dy = points[i+1][1] - points[i][1]
        dist = math.hypot(dx, dy)
        distances.append(dist)
        vectors.append((dx, dy, dist))
        
    # 2. Вычисляем углы изменения направления между смежными векторами
    for i in range(len(vectors) - 1):
        dx1, dy1, len1 = vectors[i]
        dx2, dy2, len2 = vectors[i+1]
        
        if len1 > 0 and len2 > 0:
            # Скалярное произведение векторов
            dot_product = dx1 * dx2 + dy1 * dy2
            cos_angle = dot_product / (len1 * len2)
            cos_angle = max(-1.0, min(1.0, cos_angle)) # Защита от погрешностей float
            angle_rad = math.acos(cos_angle)    # arccos
            angle_deg = math.degrees(angle_rad)
            angles.append(angle_deg)
            
    # Расчет статистических метрик
    mean_dist = sum(distances) / len(distances) if distances else 0
    max_dist = max(distances) if distances else 0
    mean_angle = sum(angles) / len(angles) if angles else 0
    max_angle = max(angles) if angles else 0
    
    # 3. Интегральная оценка качества геометрии (Старт с 100 баллов)
    score = 100
    anomalies = []
    
    # Штраф за дикие аномалии расстояний (если максимальный шаг превышает средний более чем в 8 раз)
    if mean_dist > 0 and (max_dist / mean_dist) > 8.0:
        score -= 30
        anomalies.append(f"Обнаружены резкие скачки координат (Max/Mean шаг = {max_dist/mean_dist:.1f})")
        
    # Штраф за угловой хаос (средний угол излома дороги нормальной сети обычно в пределах 10-25 градусов)
    if mean_angle > 45.0:
        score -= 40
        anomalies.append(f"Траектория хаотично изломана (Средний угол поворота = {mean_angle:.1f}°)")
    elif mean_angle > 25.0:
        score -= 15
        anomalies.append(f"Повышенная извилистость геометрии (Средний угол поворота = {mean_angle:.1f}°)")
        
    if max_angle > 150.0:
        score -= 20
        anomalies.append(f"Зафиксированы мертвые петли/развороты на 180° (Max угол = {max_angle:.1f}°)")
        
    score = max(0, score)
    
    # Вынесение автоматического вердикта
    if score >= 75:
        verdict = f"🟢 УСПЕШНО (Плавная нитка дороги). Точность сборки: {score}/100"
    elif score >= 40:
        verdict = f"🟡 ПОДОЗРИТЕЛЬНО (Возможен сдвиг фазы бит / неверный Endianness). Точность: {score}/100"
    else:
        verdict = f"🔴 ОТКЛОНЕНО (Белый шум / Хаос). Точность: {score}/100"
        
    print(f"\n=== ВЕРДИКТ ВАЛИДАТОРA ГЕОМЕТРИИ ===")
    print(verdict)
    print(f"Средняя длина шага между точками: {mean_dist:.2f}")
    print(f"Максимальный прыжок координаты:   {max_dist:.2f}")
    print(f"Средний угол излома линии:        {mean_angle:.2f}°")
    if anomalies:
        print("Зафиксированные аномалии структуры:")
        for anomaly in anomalies:
            print(f"  - {anomaly}")
    print("====================================")
    
    return score


def decode_and_validate_zone1(zone1_bytes, weights_table, expected_points=516):
    """
    Полный цикл: декодирование побайтового Хаффмана, 
    сборка UInt16 пар координат и их математическая валидация.
    """
    lookup = generate_huffman_lookup(weights_table)
    bit_string = "".join(f"{byte:08b}" for byte in zone1_bytes)
    
    unpacked_bytes = bytearray()
    current_bits = ""
    required_bytes_count = expected_points * 4
    
    # Escape-механизм для расширения до 0-255 диапазона
    ESCAPE_VALUE = 0x59 
    bit_iterator = iter(bit_string)
    
    try:
        for bit in bit_iterator:
            current_bits += bit
            if current_bits in lookup:
                val = lookup[current_bits]
                if val == ESCAPE_VALUE:
                    raw_byte_bits = "".join(next(bit_iterator) for _ in range(8))
                    unpacked_bytes.append(int(raw_byte_bits, 2))
                else:
                    unpacked_bytes.append(val)
                current_bits = ""
                if len(unpacked_bytes) >= required_bytes_count:
                    break
    except StopIteration:
        pass
                
    # Сборка в 16-битные координаты (Big-Endian)
    points = []
    ptr = 0
    while ptr + 4 <= len(unpacked_bytes):
        x_val = int.from_bytes(unpacked_bytes[ptr:ptr+2], byteorder='big')
        y_val = int.from_bytes(unpacked_bytes[ptr+2:ptr+4], byteorder='big')
        points.append((x_val, y_val))
        ptr += 4
        
    # Запускаем математический анализатор на полученном массиве точек
    validate_road_smoothness(points)
    
    return points

# --- ЗАПУСК НА ТЕСТОВОМ ДАМПЕ ---
extracted_weights_table = {
    "0x0000": 12, "0x0001": 16, "0x0002": 8,  "0x0003": 28, "0x0004": 8,
    "0x0005": 16, "0x0006": 8,  "0x0007": 32, "0x0008": 26, "0x0009": 6,
    "0x000A": 116,"0x000B": 6,  "0x000C": 4,  "0x000D": 48, "0x000E": 8,
    "0x000F": 8,  "0x0010": 60, "0x0011": 4,  "0x0012": 6,  "0x0013": 8,
    "0x0014": 6,  "0x0015": 6,  "0x0016": 372,"0x0017": 28, "0x0018": 352,
    "0x0019": 12, "0x001A": 96, "0x001B": 84, "0x001C": 4,  "0x001D": 8,
    "0x001E": 24, "0x001F": 56, "0x0020": 16, "0x0021": 4,  "0x0022": 4,
    "0x0023": 4,  "0x0024": 20, "0x0025": 4,  "0x0026": 8,  "0x0027": 12,
    "0x0028": 12, "0x0029": 4,  "0x002A": 48, "0x002B": 8,  "0x002C": 8,
    "0x002D": 32, "0x002E": 40, "0x002F": 12, "0x0030": 8,  "0x0031": 28,
    "0x0032": 32, "0x0033": 16, "0x0034": 8,  "0x0035": 16, "0x0036": 10,
    "0x0037": 4,  "0x0038": 4,  "0x0039": 20, "0x003A": 4,  "0x003B": 10,
    "0x003C": 52, "0x003D": 20, "0x003E": 24, "0x003F": 10, "0x0040": 6,
    "0x0041": 24, "0x0042": 28, "0x0043": 4,  "0x0044": 16, "0x0045": 100,
    "0x0046": 16, "0x0047": 4,  "0x0048": 4,  "0x0049": 8,  "0x004A": 20,
    "0x004B": 8,  "0x004C": 12, "0x004D": 28, "0x004E": 4,  "0x004F": 16,
    "0x0050": 40, "0x0051": 16, "0x0052": 4,  "0x0053": 4,  "0x0054": 8,
    "0x0055": 24, "0x0056": 12, "0x0057": 4,  "0x0058": 4,  "0x0059": 2,
    "0x008A": 1,  "0x0097": 16, "0x009D": 22
}

zone1_bytes_data = b'+\xda\x1b.\x95,\xa8ZJ\x10DL-\x135\xb9\xc8?\xae\xfc\x94\xeaI\xee+' # Ваш бинарник

# Запуск декодирования и автоматической экспертизы плавности
coords_result = decode_and_validate_zone1(zone1_bytes_data, extracted_weights_table, expected_points=516)
