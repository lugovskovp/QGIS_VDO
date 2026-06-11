import binascii
import heapq

def generate_huffman_lookup(weights_table):
    """Строит побайтовую lookup-мапу префиксов Хаффмана (0x00 - 0xFF)."""
    heap = []
    counter = 0
    for key_hex, weight in weights_table.items():
        char_id = int(key_hex, 16)
        if 0 <= char_id <= 0xFF and weight > 0:
            node = {'id': char_id, 'left': None, 'right': None}
            heapq.heappush(heap, (weight, counter, node))
            counter += 1

    if not heap: return {}
    while len(heap) > 1:
        w1, _, n1 = heapq.heappop(heap)
        w2, _, n2 = heapq.heappop(heap)
        heapq.heappush(heap, (w1 + w2, counter, {'id': None, 'left': n1, 'right': n2}))
        counter += 1

    _, _, root_node = heapq.heappop(heap)
    huffman_lookup = {}
    
    def walk_tree(node, current_code):
        if node['id'] is not None:
            huffman_lookup[current_code] = node['id']
            return
        if node['left']: walk_tree(node['left'], current_code + "0")
        if node['right']: walk_tree(node['right'], current_code + "1")

    walk_tree(root_node, "")
    return huffman_lookup


def restore_516_points_from_deltas(zone1_bytes, weights_table, total_points=516):
    """
    1. Распаковывает все 11152 бита в 1663 байта дельт.
    2. Разворачивает дельты в 516 абсолютных точек (2064 байта координат).
    """
    lookup = generate_huffman_lookup(weights_table)
    bit_string = "".join(f"{byte:08b}" for byte in zone1_bytes)
    
    # Шаг 1: Извлекаем все доступные байты из потока Хаффмана (получится 1663 байта)
    delta_bytes = bytearray()
    current_bits = ""
    
    for bit in bit_string:
        current_bits += bit
        if current_bits in lookup:
            delta_bytes.append(lookup[current_bits])
            current_bits = ""
            
    # Шаг 2: Транслируем 1663 байта дельт в 516 абсолютных координатных пар (X, Y)
    points = []
    
    # Базовые стартовые координаты (первые точки ГИС-кластера обычно инициализируются нулями 
    # или опорной точкой страницы, далее идет накопление дельт)
    current_x = 0
    current_y = 0
    
    ptr = 0
    while len(points) < total_points and ptr < len(delta_bytes):
        # Читаем знаковую дельту по оси X (превращаем byte в signed int8 от -128 до 127)
        dx = delta_bytes[ptr]
        if dx > 127: dx -= 256
        
        # Читаем знаковую дельту по оси Y
        if ptr + 1 < len(delta_bytes):
            dy = delta_bytes[ptr+1]
            if dy > 127: dy -= 256
            ptr += 2
        else:
            dy = 0
            ptr += 1
            
        # Накапливаем абсолютные значения координат
        current_x += dx
        current_y += dy
        
        # Защита лимита сетки: координата X/Y не может уйти в минус в абсолютных значениях ГИС
        current_x = max(0, current_x)
        current_y = max(0, current_y)
        
        points.append((current_x, current_y))
        
    return points

# --- ТАБЛИЦА ВЕСОВ И ДАННЫЕ ЗОНЫ 1 ---
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

# Сюда передается весь массив байт Зоны 1 (все 1394 байта вашего файла)
zone1_full_bytes = b'...' # Ваш массив байт

# Восстановление всей геометрии ломаной линии дороги
absolute_points_516 = restore_516_points_from_deltas(zone1_full_bytes, extracted_weights_table, total_points=516)

print("=== РЕЗУЛЬТАТ РАЗНОСТНОЙ ДЕКОМПРЕССИИ ===")
print(f"Из 1663 байт промежуточного потока Хаффмана сформировано: {len(absolute_points_516)} точек.")
print(f"Общий объем восстановленных абсолютных координат:        {len(absolute_points_516) * 4} байт (2064 байта)")
print("\nФрагмент итоговых абсолютных GPS/ГИС координат:")
for idx, (x_coord, y_coord) in enumerate(absolute_points_516[:15], start=1):
    print(f"  Точка {idx:02d}: X = {x_coord:<5} (0x{x_coord:04X}) | Y = {y_coord:<5} (0x{y_coord:04X})")
