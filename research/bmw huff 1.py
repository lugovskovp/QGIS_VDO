import binascii
import heapq

def generate_huffman_lookup(weights_table):
    """
    Автоматически строит классическое дерево Хаффмана на основе весов
    и генерирует словарь соответствия: 'бинарный_код' -> 'символ'
    """
    # Создаем очередь с приоритетами (кучу) из одиночных узлов
    # Формат элемента: [вес, счетчик_для_уникальности, узел]
    # Нам нужны только символы в диапазоне от 0x00 до 0xFF
    heap = []
    counter = 0
    for key_title, weight in weights_table.items():
        # Извлекаем числовое значение ID из текстового заголовка (например, "0x41 ('A')" -> 0x41)
        if "0x" in key_title:
            try:
                hex_part = key_title.split()[0].replace("0x", "")
                char_id = int(hex_part, 16)
                heapq.heappush(heap, (weight, counter, {'id': char_id, 'left': None, 'right': None}))
                counter += 1
            except ValueError:
                continue

    if not heap:
        return {}

    # Строим дерево, объединяя два узла с наименьшим весом
    while len(heap) > 1:
        weight1, _, node1 = heapq.heappop(heap)
        weight2, _, node2 = heapq.heappop(heap)
        
        parent_node = {'id': None, 'left': node1, 'right': node2}
        parent_weight = weight1 + weight2
        
        heapq.heappush(heap, (parent_weight, counter, parent_node))
        counter += 1

    # Извлекаем корень дерева
    _, _, root_node = heap[0]

    huffman_lookup = {}
    
    # Рекурсивный обход дерева для сборки бинарных кодов ('0' - лево, '1' - право)
    def walk_tree(node, current_code):
        if node['id'] is not None:
            char_id = node['id']
            # Маппинг символов: если это латиница верхнего регистра (0x41-0x5A), 
            # переводим её в нижний регистр (a-z) для чтения названий улиц
            if 0x41 <= char_id <= 0x5A:
                char_out = chr(char_id).lower()
            elif 32 <= char_id <= 126:
                char_out = chr(char_id)
            elif char_id == 0x00:
                char_out = "[EOS]" # Маркер конца строки
            else:
                char_out = f"[{char_id}]" # Служебный токен префикса
                
            huffman_lookup[current_code] = char_out
            return
        
        if node['left']:
            walk_tree(node['left'], current_code + "0")
        if node['right']:
            walk_tree(node['right'], current_code + "1")

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

from vdo.constants import huffman_bytes_weights_table

# Тестовый фрагмент бинарного потока
compressed_data_hex = "04604820f0f9c23c58400f4eeec3d7a3"

# Запуск декодирования с автоматической генерацией кодового дерева
# result_text = decode_bit_stream(compressed_data_hex, sample_huffman_table)
result_text = decode_bit_stream(compressed_data_hex, huffman_bytes_weights_table)

print("--- ТЕСТ АВТОМАТИЧЕСКОЙ СБОРКИ И ДЕКОДИРОВАНИЯ ---")
print("Сгенерированные бинарные коды (примеры в памяти):")
generated_codes = generate_huffman_lookup(sample_huffman_table)
for code, char in list(generated_codes.items())[:10]: # Покажем первые 10 кодов
    print(f"  Биты '{code}' => Символ '{char}'")

print("\nРезультат декодирования строки:", result_text)
