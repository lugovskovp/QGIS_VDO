import binascii
import heapq

import heapq

def generate_huffman_lookup(weights_table):
    """
    Автоматически строит дерево Хаффмана на основе таблицы весов
    для ключей в диапазоне от 0x0000 до 0xA000.
    
    Возвращает словарь соответствия: { 'бинарный_код_строкой': декодированное_значение }
    """
    # Очередь с приоритетами (куча) для сборки дерева
    # Формат элемента: (вес, уникальный_счетчик, узел_дерева)
    heap = []
    counter = 0
    
    for key_title, weight in weights_table.items():
        # Извлекаем числовое значение ID из текстового ключа (например, "0x0410 ('А')" -> 0x0410)
        if "0x" in key_title:
            try:
                hex_part = key_title.split()[0].replace("0x", "")
                char_id = int(hex_part, 16)
                
                # Фильтр диапазона от 0x0000 до 0xA000 и исключение нулевых весов
                if 0 <= char_id <= 0xA000 and weight > 0:
                    node = {'id': char_id, 'left': None, 'right': None}
                    heapq.heappush(heap, (weight, counter, node))
                    counter += 1
            except (ValueError, IndexError):
                continue

    if not heap:
        return {}

    # Построение дерева Хаффмана путем слияния минимальных узлов
    while len(heap) > 1:
        weight1, _, node1 = heapq.heappop(heap)
        weight2, _, node2 = heapq.heappop(heap)
        
        parent_node = {'id': None, 'left': node1, 'right': node2}
        parent_weight = weight1 + weight2
        
        heapq.heappush(heap, (parent_weight, counter, parent_node))
        counter += 1

    # Корень финального дерева
    _, _, root_node = heap
    huffman_lookup = {}
    
    # Рекурсивный обход дерева для генерации префиксных битовых кодов
    def walk_tree(node, current_code):
        if node['id'] is not None:
            val_id = node['id']
            
            # Логика интерпретации ID в конечный символ или токен
            if val_id == 0x00:
                char_out = "[EOS]"                      # Маркер конца строки
            elif 0x41 <= val_id <= 0x5A:
                char_out = chr(val_id).lower()          # Перевод латиницы A-Z в нижний регистр a-z
            elif 32 <= val_id <= 126:
                char_out = chr(val_id)                  # Остальной печатный ASCII
            elif 0x0400 <= val_id <= 0x04FF:
                char_out = chr(val_id)                  # Кириллица (Unicode), если присутствует в СНГ-версии
            else:
                char_out = f"[Token_0x{val_id:04X}]"    # Крупные токены координат или гео-префиксов
                
            huffman_lookup[current_code] = char_out
            return
        
        # Левая ветка кодируется нулем, правая — единицей
        if node['left']:
            walk_tree(node['left'], current_code + "0")
        if node['right']:
            walk_tree(node['right'], current_code + "1")

    # Запускаем обход от корня
    walk_tree(root_node, "")
    return huffman_lookup

def decode_bit_stream(hex_compressed, weights_table):
    """
    Модифицированная функция декодирования:
    1. Генерирует huffman_lookup на лету из таблицы весов
    2. Разворачивает байты в биты
    3. Восстанавливает текст
    """
    # Шаг 1: Автогенерация кодов Хаффмана от a до z (и служебных токенов)
    huffman_lookup = generate_huffman_lookup(weights_table)
    
    # Шаг 2: Переводим HEX-дамп в битовую ленту
    binary_str = binascii.unhexlify(hex_compressed.replace(" ", ""))
    bit_string = "".join(f"{byte:08b}" for byte in binary_str)
    
    decoded_output = []
    current_bits = ""
    
    # Шаг 3: Побитовое чтение и сопоставление со сгенерированным словарем
    for bit in bit_string:
        current_bits += bit
        if current_bits in huffman_lookup:
            char = huffman_lookup[current_bits]
            if char == "[EOS]":
                break
            decoded_output.append(char)
            current_bits = "" # Очистка буфера под следующий символ
            
    return "".join(decoded_output)

# --- ИСХОДНЫЕ ДАННЫЕ ДЛЯ ПРОВЕРКИ ---

# Наш ранее собранный huffman_table (результат работы функции parse_carin_slice)
# Заполняем весами, которые были получены из среза заголовка 0xA6 - 0x21A
sample_huffman_table = {
    "0x00": 2, "0x01": 12, "0x02": 16, "0x03": 8, "0x04": 28, "0x0D": 4, 
    "0x41 ('A')": 6, "0x42 ('B')": 24, "0x43 ('C')": 28, "0x44 ('D')": 4, 
    "0x45 ('E')": 16, "0x46 ('F')": 100, "0x47 ('G')": 16, "0x48 ('H')": 4, 
    "0x49 ('I')": 4, "0x4A ('J')": 8, "0x4B ('K')": 20, "0x4C ('L')": 8, 
    "0x4D ('M')": 12, "0x4E ('N')": 28, "0x4F ('O')": 4, "0x50 ('P')": 16, 
    "0x51 ('Q')": 40, "0x52 ('R')": 16, "0x53 ('S')": 4, "0x54 ('T')": 4, 
    "0x55 ('U')": 8, "0x56 ('V')": 24, "0x57 ('W')": 12, "0x58 ('X')": 4, 
    "0x59 ('Y')": 4, "0x5A ('Z')": 2
}

# Тестовый фрагмент бинарного потока
compressed_data_hex = "04604820f0f9c23c58400f4eeec3d7a3"

compressed_data_hex = b'+\xda\x1b.\x95,\xa8ZJ\x10DL-\x135\xb9\xc8?\xae\xfc\x94\xeaI\xee+\x1c\xef\x18\xf0q\x85\xfb.\x11L\x91E\xc1X\xadJ\xcda\xf4~+\x84]\xae@\x0c[\xe16\xe2\xa1\x08QH\x8aG\x01\xa6$W\x14a\x9a\x89\x0c\x8a\xe1`\x84\x89\xaaq\x94?@\xa6\x8d\r\xdfG\xc2\xe8\x8d\x04](\xdasC\x02t\xa0\xe0\xafC\xc7~\x18A\x18N\x91\xc0\xd3\xfc\x0f\x05\r\x13\xac\x85\x05E\x85R\x01\x0b\x84*\x18\x01\x01\xd0\x8f\x8dg\x049(I\xd3\x0cg\xccJ\x01$\xf4H;#\x83\xa5\'`\x88tn\x89\xb0$oB\x81\xe1@\x1e\x9d\x92B\x0b\xce\x18)A\xa2\xa0.(P\x13V%4%\x12\xa2\x0c\x80\x04h\xbf\x10\x94\xa0\x00= J\xa8rsD\x15h\xc9\x15\x07\xa1&\t\x1f\xabZ\x08F2D\x91\x88\x01\xa6\xe5OK\xe6S/\x81d\xe2\x9b+p\x9a \xc2\xf9\xfb\x15C\x19\x11\x04#8\xa3)\'\x94i4a\xc0=1\xe5\xech\xe9*\xe8"\t\x10C\xc9-K$\x8c\x0b\x91\x91\xa6J\x1a1z\x9aH\xc8\xd9\x18\xee\x94(\x83Q&\xd9\xcd$t\x03\x16$5A\x9a%\xd4G\xb1\xa1\x15\xc9\xa8R\x06\x10\x9eQ\xf9\xa7\x02\xea,\x92\x9fC\xbd\xd2\x05@x\xd7(\xe3\xbc\x8a\x88\xba\xc2\xbc\xbc\x87EDL2\xa0\xc1"+\x0b}\x15\xe6J\x8b\xd2n\x94\xc2\xf0\xee8\x11\xc90r<\x992h\x8a3\xc2\xa3(|\x07\xe0\xec\xbb\x9f\xea\xac<yO\xe1\xca-\x92\xd0\x98\xa1\x82\xe8\xaaFj\xc8\xd5\xfa?\x18%\xfa\x0b\x95\x97\x0e\xe0x\xe0r\x97\xa0\t\xc81\xb7\xc7\x1aV\x10\x1bCx"3\x17\x82\xf04W\x8f0M}\nW\x03]5\x1a\x08\xd1b\x98\r&\x98dh\x16\x88\xd8 \x14\xc3\xf0\xc4\x0f\x002\t\xcc\x85\xa3\x0e\xc9:FF\xc1\x17\x99\x021\xac&\x18\x07\xba\x9b\x19Ay$\xc9\xcf0|\x1d\x90C\xb4\xb91d\x10\xe3\x0e\x02\x89\x16GB1z$\x14\x11 v\x03\xdb\x100(\x8f$\x9b\xd0:\xe59\x80L\xd9\x8a\x12Bj\x83\x908S \x88\xc1\x94\x9b\x81b\xf9\x83\x1d\r\x88j8\xc1\xe2*w\x96\xe0\t&\x9c\x92\xd9`p\xcfYk\xfc@\xa50\xae+\xc0y8\x10\x05\xe1yt\'\xa1\xc2\x90\xc0B\x0e\n\xb2\xa89\x8fD8\xf4\xb7\xa3\xa4\xa89-cQ\xa0+\x0cC\xf9\x06P\x82\xc0i\x00=\x9c\xe2\xf4.\x84\xb2\xc2>\xc6\xe8\x97"\xa48;\x01\xc9B \xe8*\xda\xe3\xa8\x0b\x02L\x01U\xe2\x1d\xdb2\x01\t:\xc48\x10\xda\x9e\x19\xeb!ZwG\x93\x88f\x12\x90TdC\x16\xc7\xbd\x0c\xe4\xd1X\xc2apFT\xcdh\xe6D\x8c\xd0\xa9\x08\x04\x13\xc8\xf3\x0b\x88\x11\x80"\x88\xe8\x10\x82\xb3.)e0\x18G\xd1\xf8\x9a\x84\x90nF\x8a\xc4*\xa4o\x14\x03n\x9f\xa0\xdb\xc1Hn_\x8d\xc7\xe1XQ\r:\xa9ZTi\x89\x0c\xa4\x081`\xdf4\xac^&\x10,i\x16V\x00<\xcb\x93\xc1\x0c\xda7\xae\xcc\xf2\x93Ad\'\x91r\xd6\x93H\xda\x1d$B\xb8s;\xa6`\xdc\x01\xad\xf1\x84m\x07\xe2\xb8\xf0\x8c@a\x98\x86\xe8\x1c\x0c\xe7\x18\x8f4B\x97\x96&\xafA\xd1(\x1e3\xf1\x02\x7fI\xd0\x8e6WzjvF\x89\x13\x0c\xc1\x00\xa2\x8f\xc1\xc0f+\xc9!\xba.I\x98\xb6\x0c@J?)\x85\xb8\x8f&"\xe8TcHQ\xd2A\xc4\xbaq!\xa2\xc0S5\xa8`+\x0ebT-\xa0\xf0\x8a.\x940\xf3\xc0\x00\xc8\'\x00\x0chn\x85\xc1\t\xbb-\xa2\xbcX\x98\xb2\xce\xbaKH\xbf\x1ad\xf4\xba\x93\xb2\x92\x1d\xc1\xc9\xb5\x13\xe4\\+\x8dR:eH\xbaE\x1ed\xcc\x12\x9eR\x9e\x8c\xc3(\x13#a\xec>\xa0\xf3^\xb5\xc7\xf9s\tz\xdb8\x87A\xe2OU3\x0e\'\x84\x10\x90\x92\xf65MXq*\xe3D\xad\x8cq\xc2I\xc6\x8e\x91f\x85\xcf\x88\x07\x1d\xa4D\x88\x8c\xb3^.\xd9i\xf1%$]\x92\x93\x12\xb2-\xd5\xc9\xbd\x11\xa6\x1dx\x9fq\xf6C\xc5\x89\x14\x03\xc1\xcc\xe5\x1b\x07\x86\x99\xc6Y\x9c/B\x91\xb25\x8eP\xa0qREx| \x04C\x0c\x97(\xf3pq\xd2_\x15\xd1\xec\x1f\x89\x074\xf2\x1d%l\x08\x95\x92\x8aA\xc7\x89\x9e\x1e\x80\xc3\\\xfb\x85\x13\xf8[\x98\xa2\xacJ\x0c\xa5\xd0\xd2@Gr\xa2,\xa32\x0ex\x01\x16\x14\xfc\x81\xe2|n\x1bclM\x93\xb12\x8b\xc0zL\x1d\xd4\x11\xc84\x8f\xe8\xec)\x98q\x95\t\xa4F<%\x84r\x0eG\x80V\x90\x00\x00\r\xf9\xe8A\x15$\xf4\x80%#\x84\xa9\x8a1\xe6\x8f\xcfL\x90,4\xa6\x014\x13\x01b\xe0\xf5\x0b\x83\x18\xf46\xe0\x00\x18\x1dy\x05\tJ\xd9}\x81\xa4\xc5f\xa6W\x0e \xea\xde a \xf1^\x04\x8fJ\x93\xbcG\x17,i\x1d\x87\xb0\x07\'\xb4\x1e\\@B\x18k\x9b"\x01\xd8\x01\xc7\x01\xc6Z\xc2\xb0\xec\xbe#c`t+\x11\x0b"\xfa\x0eR\x88\xa0/\x82X\xaf\x186rC"\x82,$\xb0\xec\xd2\x0f\xa0\x88\xfc\xe5\x8d \x84\x93\x9a0\x0e}\xca\x92:\x06c\x85\xb0\xf5\xb3\xac\xd0v\x0e\x92\xb1\xc7!\x18\x96\xac\x89\n9\x88m\xb8\xc6.D\x05X\x0b\x1d\xc8\xc2\xa6\x14\xc5\x02\xd4;\x03\xa3\xe1\xeb\x94\xd9\x90\xca\xb0\x0c\xb2F\xb8S\x0f\xd9\xc8\xfeSE\x93\xda\x06\xb11bC\x90\x02\x01\x11\x16F\xc2^\x03\xaa\x90\x89\x16\n\x15\x88ZrDs\x0cZ`\xa1\xba\xbf\x01\xb9\x93\xcc\r$\xc2\xa0p\xceAA8w\x17\xe4u\r\x97\x93\x12\x1f\xe0\x00\x00\x04`H \xf0\xf9\xc2<X@\x0fN\xeec\xd7\xa3x\xd0g\xea\x182\xa7\xeat\x96\x8f\xd7\xa1\xd2\xe8\xbe\x06\xdf\xa9\xe8\xfdz\x1d.\x8b\xf4+O\xb4\x12f\xb4\xd2}\x83\xdfH\xa9\xeb\xb9\x87\xb6\xec\\0\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\x18\x11X1\xa6c\x94\xc7\xb1\x16"\xd4\\\x8b\xd1\x80\x00\x00\x00\x00\x00\x00'

# Запуск декодирования с автоматической генерацией кодового дерева
result_text = decode_bit_stream(compressed_data_hex, sample_huffman_table)

print("--- ТЕСТ АВТОМАТИЧЕСКОЙ СБОРКИ И ДЕКОДИРОВАНИЯ ---")
print("Сгенерированные бинарные коды (примеры в памяти):")
generated_codes = generate_huffman_lookup(sample_huffman_table)
for code, char in list(generated_codes.items())[:10]: # Покажем первые 10 кодов
    print(f"  Биты '{code}' => Символ '{char}'")

print("\nРезультат декодирования строки:", result_text)
