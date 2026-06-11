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

def decode_zone1_debug(zone1_bytes, weights_table, max_bytes=2064):
    lookup = generate_huffman_lookup(weights_table)
    bit_string = "".join(f"{byte:08b}" for byte in zone1_bytes)
    
    unpacked_bytes = bytearray()
    current_bits = ""
    
    bit_iterator = iter(bit_string)
    bits_read = 0
    
    for bit in bit_iterator:
        current_bits += bit
        bits_read += 1
        
        if current_bits in lookup:
            unpacked_bytes.append(lookup[current_bits])
            current_bits = ""
            
            if len(unpacked_bytes) >= max_bytes:
                break
                
    print("\n--- ДИАГНОСТИКА БИТОВОГО ПОТОКА ---")
    print(f"Всего бит в Зоне 1 физически: {len(bit_string)}")
    print(f"Прочитано бит до останова:    {bits_read}")
    print(f"Осталось неразобранных бит:   {len(bit_string) - bits_read}")
    if current_bits:
        print(f"Бит-тупик (не найден в дереве): '{current_bits}'")
    print("-----------------------------------\n")
    
    return unpacked_bytes


def decode_and_validate_absolute_coordinates(zone1_bytes, weights_table, total_points=516):
    """
    Распаковывает поток в 2064 байта и собирает абсолютные UInt16 координаты (X, Y).
    Проверяет жесткое условие: каждый четный байт (High-байт) <= 0xC0.
    """
    decode_zone1_debug(zone1_bytes, weights_table)

    lookup = generate_huffman_lookup(weights_table)
    bit_string = "".join(f"{byte:08b}" for byte in zone1_bytes)
    
    unpacked_bytes = bytearray()
    current_bits = ""
    required_bytes_count = total_points * 4
    
    

    # 1. Распаковка потока Хаффмана в байты
    for bit in bit_string:
        current_bits += bit
        if current_bits in lookup:
            unpacked_bytes.append(lookup[current_bits])
            current_bits = ""
            if len(unpacked_bytes) >= required_bytes_count:
                break
                
    # 2. Математическая верификация: проверка четных байт (индексы 0, 2, 4...)
    verified_even_rules = True
    failed_at_index = -1
    
    for idx in range(0, len(unpacked_bytes), 2):
        if unpacked_bytes[idx] > 0xC0:
            verified_even_rules = False
            failed_at_index = idx
            break
            
    # 3. Сборка в абсолютные 16-битные координаты (X, Y) по схеме Big-Endian
    points = []
    ptr = 0
    while ptr + 4 <= len(unpacked_bytes):
        # Старший байт сдвигаем на 8 бит влево и склеиваем с младшим байтом
        x_abs = (unpacked_bytes[ptr] << 8) | unpacked_bytes[ptr+1]
        y_abs = (unpacked_bytes[ptr+2] << 8) | unpacked_bytes[ptr+3]
        points.append((x_abs, y_abs))
        ptr += 4
        
    # Вывод результатов автоматической экспертизы структуры
    print("=== ЭКСПЕРТИЗА СТРУКТУРЫ АБСОЛЮТНЫХ КООРДИНАТ ===")
    print(f"Всего распаковано байт из Зоны 1: {len(unpacked_bytes)} из 2064")
    print(f"Сформировано абсолютных точек:  {len(points)} из 516")
    
    if verified_even_rules:
        print("Валидация High-байта (каждый чётный байт <= 0xC0): 🟢 ПОДТВЕРЖДЕНО")
    else:
        print(f"Валидация провалена: 🔴 СБОЙ на чётном индексе {failed_at_index} (значение: 0x{unpacked_bytes[failed_at_index]:02X} > 0xC0)")
    print("=================================================")
    
    return points

# --- ОДНОБАЙТОВАЯ ТАБЛИЦА ВЕСОВ И СТРИМ ДАННЫХ ИЗ ВАШЕГО ФАЙЛА ---
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






# Массив байт Зоны 1 (все 1394 байта вашего файла)
zone1_full_bytes = b'+\xda\x1b.\x95,\xa8ZJ\x10DL-\x135\xb9\xc8?\xae\xfc\x94\xeaI\xee+\x1c\xef\x18\xf0q\x85\xfb.\x11L\x91E\xc1X\xadJ\xcda\xf4~+\x84]\xae@\x0c[\xe16\xe2\xa1\x08QH\x8aG\x01\xa6$W\x14a\x9a\x89\x0c\x8a\xe1`\x84\x89\xaaq\x94?@\xa6\x8d\r\xdfG\xc2\xe8\x8d\x04](\xdasC\x02t\xa0\xe0\xafC\xc7~\x18A\x18N\x91\xc0\xd3\xfc\x0f\x05\r\x13\xac\x85\x05E\x85R\x01\x0b\x84*\x18\x01\x01\xd0\x8f\x8dg\x049(I\xd3\x0cg\xccJ\x01$\xf4H;#\x83\xa5\'`\x88tn\x89\xb0$oB\x81\xe1@\x1e\x9d\x92B\x0b\xce\x18)A\xa2\xa0.(P\x13V%4%\x12\xa2\x0c\x80\x04h\xbf\x10\x94\xa0\x00= J\xa8rsD\x15h\xc9\x15\x07\xa1&\t\x1f\xabZ\x08F2D\x91\x88\x01\xa6\xe5OK\xe6S/\x81d\xe2\x9b+p\x9a \xc2\xf9\xfb\x15C\x19\x11\x04#8\xa3)\'\x94i4a\xc0=1\xe5\xech\xe9*\xe8"\t\x10C\xc9-K$\x8c\x0b\x91\x91\xa6J\x1a1z\x9aH\xc8\xd9\x18\xee\x94(\x83Q&\xd9\xcd$t\x03\x16$5A\x9a%\xd4G\xb1\xa1\x15\xc9\xa8R\x06\x10\x9eQ\xf9\xa7\x02\xea,\x92\x9fC\xbd\xd2\x05@x\xd7(\xe3\xbc\x8a\x88\xba\xc2\xbc\xbc\x87EDL2\xa0\xc1"+\x0b}\x15\xe6J\x8b\xd2n\x94\xc2\xf0\xee8\x11\xc90r<\x992h\x8a3\xc2\xa3(|\x07\xe0\xec\xbb\x9f\xea\xac<yO\xe1\xca-\x92\xd0\x98\xa1\x82\xe8\xaaFj\xc8\xd5\xfa?\x18%\xfa\x0b\x95\x97\x0e\xe0x\xe0r\x97\xa0\t\xc81\xb7\xc7\x1aV\x10\x1bCx"3\x17\x82\xf04W\x8f0M}\nW\x03]5\x1a\x08\xd1b\x98\r&\x98dh\x16\x88\xd8 \x14\xc3\xf0\xc4\x0f\x002\t\xcc\x85\xa3\x0e\xc9:FF\xc1\x17\x99\x021\xac&\x18\x07\xba\x9b\x19Ay$\xc9\xcf0|\x1d\x90C\xb4\xb91d\x10\xe3\x0e\x02\x89\x16GB1z$\x14\x11 v\x03\xdb\x100(\x8f$\x9b\xd0:\xe59\x80L\xd9\x8a\x12Bj\x83\x908S \x88\xc1\x94\x9b\x81b\xf9\x83\x1d\r\x88j8\xc1\xe2*w\x96\xe0\t&\x9c\x92\xd9`p\xcfYk\xfc@\xa50\xae+\xc0y8\x10\x05\xe1yt\'\xa1\xc2\x90\xc0B\x0e\n\xb2\xa89\x8fD8\xf4\xb7\xa3\xa4\xa89-cQ\xa0+\x0cC\xf9\x06P\x82\xc0i\x00=\x9c\xe2\xf4.\x84\xb2\xc2>\xc6\xe8\x97"\xa48;\x01\xc9B \xe8*\xda\xe3\xa8\x0b\x02L\x01U\xe2\x1d\xdb2\x01\t:\xc48\x10\xda\x9e\x19\eb!ZwG\x93\x88f\x12\x90TdC\x16\xc7\xbd\x0c\xe4\xd1X\xc2apFT\xcdh\xe6D\x8c\xd0\xa9\x08\x04\x13\xc8\xf3\x0b\x88\x11\x80"\x88\xe8\x10\x82\xb3.)e0\x18G\xd1\xf8\x9a\x84\x90nF\x8a\xc4*\xa4o\x14\x03n\x9f\xa0\xdb\xc1Hn_\x8d\xc7\xe1XQ\r:\xa9ZTi\x89\x0c\xa4\x081`\xdf4\xac^&\x10,i\x16V\x00<\xcb\x93\xc1\x0c\xda7\xae\xcc\xf2\x93Ad\'\x91r\xd6\x93H\xda\x1d$B\xb8s;\xa6`\xdc\x01\xad\xf1\x84m\x07\xe2\xb8\xf0\x8c@a\x98\x86\xe8\x1c\x0c\xe7\x18\x8f4B\x97\x96&\xafA\xd1(\x1e3\xf1\x02\x7fI\xd0\x8e6WzjvF\x89\x13\x0c\xc1\x00\xa2\x8f\xc1\xc0f+\xc9!\xba.I\x98\xb6\x0c@J?)\x85\xb8\x8f&"\xe8TcHQ\xd2A\xc4\xbaq!\xa2\xc0S5\xa8`+\x0ebT-\xa0\xf0\x8a.\x940\xf3\xc0\x00\xc8\'\x00\x0chn\x85\xc1\t\xbb-\xa2\xbcX\x98\xb2\xce\xbaKH\xbf\x1ad\xf4\xba\x93\xb2\x92\x1d\xc1\xc9\xb5\x13\xe4\\+\x8dR:eH\xbaE\x1ed\xcc\x12\x9eR\x9e\x8c\xc3(\x13#a\xec>\xa0\xf3^\xb5\xc7\xf9s\tz\xdb8\x87A\xe2OU3\x0e\'\x84\x10\x90\x92\xf65MXq*\xe3D\xad\x8cq\xc2I\xc6\x8e\x91f\x85\xcf\x88\x07\x1d\xa4D\x88\x8c\xb3^.\xd9i\xf1%$]\x92\x93\x12\xb2-\xd5\xc9\xbd\x11\xa6\x1dx\x9fq\xf6C\xc5\x89\x14\x03\xc1\xcc\xe5\x1b\x07\x86\x99\xc6Y\x9c/B\x91\xb25\x8eP\xa0qREx| \x04C\x0c\x97(\xf3pq\xd2_\x15\xd1\xec\x1f\x89\x074\xf2\x1d%l\x08\x95\x92\x8aA\xc7\x89\x9e\x1e\x80\xc3\\\xfb\x85\x13\xf8[\x98\xa2\xacJ\x0c\xa5\xd0\xd2@Gr\xa2,\xa32\x0ex\x01\x16\x14\xfc\x81\xe2|n\x1bclM\x93\xb12\x8b\xc0zL\x1d\xd4\x11\xc84\x8f\xe8\xec)\x98q\x95\t\xa4F<%\x84r\x0eG\x80V\x90\x00\x00'



# Запуск декомпрессии абсолютных географических узлов
absolute_road_points = decode_and_validate_absolute_coordinates(zone1_full_bytes, extracted_weights_table, total_points=516)


"""
=== ЭКСПЕРТИЗА СТРУКТУРЫ АБСОЛЮТНЫХ КООРДИНАТ ===
Всего распаковано байт из Зоны 1: 1663 из 2064
Сформировано абсолютных точек:  415 из 516
Валидация High-байта (каждый чётный байт <= 0xC0): 🟢 ПОДТВЕРЖДЕНО
=================================================


--- ДИАГНОСТИКА БИТОВОГО ПОТОКА ---
Всего бит в Зоне 1 физически: 9152
Прочитано бит до останова:    9152
Осталось неразобранных бит:   0
Бит-тупик (не найден в дереве): '0000'
-----------------------------------
финальный упакованный поток геометрии, который процессор навигатора Dayton разворачивает в 516 точек (2064 байта) 
с помощью Разностного побитового кодирования переменных длин (Variable Length / Bit-Packing Delta).
"""


