import binascii
import heapq

def generate_original_huffman_lookup(weights_table):
    """Строит дерево Хаффмана строго по оригинальным 93 элементам таблицы весов."""
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

    if not heap:
        return {}

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


def decode_zone1_with_1byte_escape(zone1_bytes, weights_table, max_bytes=2064):
    """
    Распаковывает битовый поток Зоны 1 в плоскую последовательность из 2064 байт.
    При встрече токена 0x8A извлекает из итератора строго следующие 8 бит (1 сырой байт).
    """
    lookup = generate_original_huffman_lookup(weights_table)
    
    # Разворачиваем весь бинарный буфер Зоны 1 в битовую ленту
    bit_string = "".join(f"{byte:08b}" for byte in zone1_bytes)
    bit_iterator = iter(bit_string)
    
    unpacked_bytes = bytearray()
    current_bits = ""
    ESCAPE_TOKEN = 0x8A
    
    try:
        for bit in bit_iterator:
            current_bits += bit
            
            if current_bits in lookup:
                token = lookup[current_bits]
                
                if token == ESCAPE_TOKEN:
                    # ПОЙМАЛИ ESCAPE 0x8A: Читаем строго следующие 8 бит напрямую как 1 сырой байт
                    raw_bits = "".join(next(bit_iterator) for _ in range(8))
                    raw_byte = int(raw_bits, 2)
                    unpacked_bytes.append(raw_byte)
                else:
                    # Обычный однобайтовый токен из таблицы весов Хаффмана
                    unpacked_bytes.append(token)
                    
                current_bits = ""
                
                # Строгий останов при наполнении массива до 516 точек * 4 байта = 2064 байта
                if len(unpacked_bytes) >= max_bytes:
                    break
    except StopIteration:
        # Поток бит завершился раньше времени
        pass
        
    return unpacked_bytes

# --- ОДНОБАЙТОВАЯ ТАБЛИЦА ВЕСОВ И СТРИМ ИЗ ДАМПА ---
extracted_weights_table = {
    "0x01": 12, "0x02": 16, "0x03": 8,  "0x04": 28, "0x05": 8,
    "0x06": 16, "0x07": 8,  "0x08": 32, "0x09": 26, "0x0A": 6,
    "0x0B": 116,"0x0C": 6,  "0x0D": 4,  "0x0E": 48, "0x0F": 8,
    "0x10": 8,  "0x11": 60, "0x12": 4,  "0x13": 6,  "0x14": 8,
    "0x15": 6,  "0x16": 6,  "0x17": 372,"0x18": 28, "0x19": 352,
    "0x1A": 12, "0x1B": 96, "0x1C": 84, "0x1D": 4,  "0x1E": 8,
    "0x1F": 24, "0x20": 56, "0x21": 16, "0x22": 4,  "0x23": 4,
    "0x24": 4,  "0x25": 20, "0x26": 4,  "0x27": 8,  "0x28": 12,
    "0x29": 12, "0x2A": 4,  "0x2B": 48, "0x2C": 8,  "0x2D": 8,
    "0x2E": 32, "0x2F": 40, "0x30": 12, "0x31": 8,  "0x32": 28,
    "0x33": 32, "0x34": 16, "0x35": 8,  "0x36": 16, "0x37": 10,
    "0x38": 4,  "0x39": 4,  "0x3A": 20, "0x3B": 4,  "0x3C": 16,
    "0x3D": 52, "0x3E": 20, "0x3F": 24, "0x40": 10, "0x41": 6,
    "0x42": 24, "0x43": 28, "0x44": 4,  "0x45": 16, "0x46": 100,
    "0x47": 16, "0x48": 4,  "0x49": 4,  "0x4A": 8,  "0x4B": 20,
    "0x4C": 8,  "0x4D": 12, "0x4E": 28, "0x4F": 4,  "0x50": 16,
    "0x51": 40, "0x52": 16, "0x53": 4,  "0x54": 4,  "0x55": 8,
    "0x56": 24, "0x57": 12, "0x58": 4,  "0x59": 4,  "0x5A": 2,
    "0x8A": 1,  "0x97": 16, "0x9D": 22
}

# Массив байт Зоны 1 (все 1394 байта вашего файла)
zone1_full_bytes = b'...'  # Передайте сюда вашу переменную с байтами Зоны 1
# Вставьте сюда ВЕСЬ бинарный массив Зоны 1 (все 1394 байта вашего файла)
zone1_full_bytes = b'+\xda\x1b.\x95,\xa8ZJ\x10DL-\x135\xb9\xc8?\xae\xfc\x94\xeaI\xee+\x1c\xef\x18\xf0q\x85\xfb.\x11L\x91E\xc1X\xadJ\xcda\xf4~+\x84]\xae@\x0c[\xe16\xe2\xa1\x08QH\x8aG\x01\xa6$W\x14a\x9a\x89\x0c\x8a\xe1`\x84\x89\xaaq\x94?@\xa6\x8d\r\xdfG\xc2\xe8\x8d\x04](\xdasC\x02t\xa0\xe0\xafC\xc7~\x18A\x18N\x91\xc0\xd3\xfc\x0f\x05\r\x13\xac\x85\x05E\x85R\x01\x0b\x84*\x18\x01\x01\xd0\x8f\x8dg\x049(I\xd3\x0cg\xccJ\x01$\xf4H;#\x83\xa5\'`\x88tn\x89\xb0$oB\x81\xe1@\x1e\x9d\x92B\x0b\xce\x18)A\xa2\xa0.(P\x13V%4%\x12\xa2\x0c\x80\x04h\xbf\x10\x94\xa0\x00= J\xa8rsD\x15h\xc9\x15\x07\xa1&\t\x1f\xabZ\x08F2D\x91\x88\x01\xa6\xe5OK\xe6S/\x81d\xe2\x9b+p\x9a \xc2\xf9\xfb\x15C\x19\x11\x04#8\xa3)\'\x94i4a\xc0=1\xe5\xech\xe9*\xe8"\t\x10C\xc9-K$\x8c\x0b\x91\x91\xa6J\x1a1z\x9aH\xc8\xd9\x18\xee\x94(\x83Q&\xd9\xcd$t\x03\x16$5A\x9a%\xd4G\xb1\xa1\x15\xc9\xa8R\x06\x10\x9eQ\xf9\xa7\x02\xea,\x92\x9fC\xbd\xd2\x05@x\xd7(\xe3\xbc\x8a\x88\xba\xc2\xbc\xbc\x87EDL2\xa0\xc1"+\x0b}\x15\xe6J\x8b\xd2n\x94\xc2\xf0\xee8\x11\xc90r<\x992h\x8a3\xc2\xa3(|\x07\xe0\xec\xbb\x9f\xea\xac<yO\xe1\xca-\x92\xd0\x98\xa1\x82\xe8\xaaFj\xc8\xd5\xfa?\x18%\xfa\x0b\x95\x97\x0e\xe0x\xe0r\x97\xa0\t\xc81\xb7\xc7\x1aV\x10\x1bCx"3\x17\x82\xf04W\x8f0M}\nW\x03]5\x1a\x08\xd1b\x98\r&\x98dh\x16\x88\xd8 \x14\xc3\xf0\xc4\x0f\x002\t\xcc\x85\xa3\x0e\xc9:FF\xc1\x17\x99\x021\xac&\x18\x07\xba\x9b\x19Ay$\xc9\xcf0|\x1d\x90C\xb4\xb91d\x10\xe3\x0e\x02\x89\x16GB1z$\x14\x11 v\x03\xdb\x100(\x8f$\x9b\xd0:\xe59\x80L\xd9\x8a\x12Bj\x83\x908S \x88\xc1\x94\x9b\x81b\xf9\x83\x1d\r\x88j8\xc1\xe2*w\x96\xe0\t&\x9c\x92\xd9`p\xcfYk\xfc@\xa50\xae+\xc0y8\x10\x05\xe1yt\'\xa1\xc2\x90\xc0B\x0e\n\xb2\xa89\x8fD8\xf4\xb7\xa3\xa4\xa89-cQ\xa0+\x0cC\xf9\x06P\x82\xc0i\x00=\x9c\xe2\xf4.\x84\xb2\xc2>\xc6\xe8\x97"\xa48;\x01\xc9B \xe8*\xda\xe3\xa8\x0b\x02L\x01U\xe2\x1d\xdb2\x01\t:\xc48\x10\xda\x9e\x19\eb!ZwG\x93\x88f\x12\x90TdC\x16\xc7\xbd\x0c\xe4\xd1X\xc2apFT\xcdh\xe6D\x8c\xd0\xa9\x08\x04\x13\xc8\xf3\x0b\x88\x11\x80"\x88\xe8\x10\x82\xb3.)e0\x18G\xd1\xf8\x9a\x84\x90nF\x8a\xc4*\xa4o\x14\x03n\x9f\xa0\xdb\xc1Hn_\x8d\xc7\xe1XQ\r:\xa9ZTi\x89\x0c\xa4\x081`\xdf4\xac^&\x10,i\x16V\x00<\xcb\x93\xc1\x0c\xda7\xae\xcc\xf2\x93Ad\'\x91r\xd6\x93H\xda\x1d$B\xb8s;\xa6`\xdc\x01\xad\xf1\x84m\x07\xe2\xb8\xf0\x8c@a\x98\x86\xe8\x1c\x0c\xe7\x18\x8f4B\x97\x96&\xafA\xd1(\x1e3\xf1\x02\x7fI\xd0\x8e6WzjvF\x89\x13\x0c\xc1\x00\xa2\x8f\xc1\xc0f+\xc9!\xba.I\x98\xb6\x0c@J?)\x85\xb8\x8f&"\xe8TcHQ\xd2A\xc4\xbaq!\xa2\xc0S5\xa8`+\x0ebT-\xa0\xf0\x8a.\x940\xf3\xc0\x00\xc8\'\x00\x0chn\x85\xc1\t\xbb-\xa2\xbcX\x98\xb2\xce\xbaKH\xbf\x1ad\xf4\xba\x93\xb2\x92\x1d\xc1\xc9\xb5\x13\xe4\\+\x8dR:eH\xbaE\x1ed\xcc\x12\x9eR\x9e\x8c\xc3(\x13#a\xec>\xa0\xf3^\xb5\xc7\xf9s\tz\xdb8\x87A\xe2OU3\x0e\'\x84\x10\x90\x92\xf65MXq*\xe3D\xad\x8cq\xc2I\xc6\x8e\x91f\x85\xcf\x88\x07\x1d\xa4D\x88\x8c\xb3^.\xd9i\xf1%$]\x92\x93\x12\xb2-\xd5\xc9\xbd\x11\xa6\x1dx\x9fq\xf6C\xc5\x89\x14\x03\xc1\xcc\xe5\x1b\x07\x86\x99\xc6Y\x9c/B\x91\xb25\x8eP\xa0qREx| \x04C\x0c\x97(\xf3pq\xd2_\x15\xd1\xec\x1f\x89\x074\xf2\x1d%l\x08\x95\x92\x8aA\xc7\x89\x9e\x1e\x80\xc3\\\xfb\x85\x13\xf8[\x98\xa2\xacJ\x0c\xa5\xd0\xd2@Gr\xa2,\xa32\x0ex\x01\x16\x14\xfc\x81\xe2|n\x1bclM\x93\xb12\x8b\xc0zL\x1d\xd4\x11\xc84\x8f\xe8\xec)\x98q\x95\t\xa4F<%\x84r\x0eG\x80V\x90\x00\x00'


# Вызов распаковки с 1-байтовым фиксированным окном пропуска
final_result_bytes = decode_zone1_with_1byte_escape(zone1_full_bytes, extracted_weights_table, max_bytes=2064)

print(f"--- РЕЗУЛЬТАТ РАСПАКОВКИ С ОКНОМ В 1 БАЙТ ТОКЕНА ---")
print(f"Всего байт извлечено в итоговый массив: {len(final_result_bytes)} из 2064.")
print(f"Целевой лимит (516*4 байта) достигнут: {len(final_result_bytes) == 2064}")

# Валидация правила чётности High-байта (индексы 0, 2, 4, 6... <= 0xC0)
verified_even_rule = True
for idx in range(0, len(final_result_bytes), 2):
    if final_result_bytes[idx] > 0xC0:
        verified_even_rule = False
        break
print(f"Соблюдение правила High-байта (каждый чётный байт <= 0xC0): {'🟢 ДА' if verified_even_rule else '🔴 СБОЙ СДВИГА ФАЗЫ'}")
