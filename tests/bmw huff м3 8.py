import binascii
import heapq

def generate_canonical_lookup(weights_table):
    """Строит каноническую lookup-мапу: { бинарная_строка: int_байт }"""
    full_weights = {b: 1 for b in range(256)}
    for key_hex, weight in weights_table.items():
        try:
            byte_id = int(key_hex, 16)
            if 0 <= byte_id <= 255:
                full_weights[byte_id] = weight
        except ValueError:
            continue

    heap = []
    counter = 0
    for byte_id, weight in full_weights.items():
        heapq.heappush(heap, (weight, counter, {'id': byte_id, 'left': None, 'right': None}))
        counter += 1

    while len(heap) > 1:
        w1, _, n1 = heapq.heappop(heap)
        w2, _, n2 = heapq.heappop(heap)
        heapq.heappush(heap, (w1 + w2, counter, {'id': None, 'left': n1, 'right': n2}))
        counter += 1

    _, _, root_node = heapq.heappop(heap)
    code_lengths = {}
    
    def collect_lengths(node, current_depth):
        if node['id'] is not None:
            code_lengths[node['id']] = current_depth
            return
        if node['left']: collect_lengths(node['left'], current_depth + 1)
        if node['right']: collect_lengths(node['right'], current_depth + 1)

    collect_lengths(root_node, 0)
    sorted_elements = sorted(code_lengths.items(), key=lambda x: (x[1], x[0]))

    canonical_lookup = {}
    current_code_int = 0
    last_length = 0

    for byte_id, length in sorted_elements:
        if length == 0: continue
        if last_length > 0:
            current_code_int <<= (length - last_length)
        bit_code = f"{current_code_int:0{length}b}"
        canonical_lookup[bit_code] = byte_id
        current_code_int += 1
        last_length = length

    return canonical_lookup

def decode_hex_to_string(hex_string, lookup_table):
    # Очищаем и преобразуем в биты
    clean_hex = hex_string.replace(" ", "").replace("0x", "")
    
    # Пропускаем стартовые нулевые байты выравнивания, если они есть
    while clean_hex.startswith("0000"):
        clean_hex = clean_hex[4:]
        
    binary_data = binascii.unhexlify(clean_hex)
    bit_string = "".join(f"{byte:08b}" for byte in binary_data)
    
    decoded_chars = []
    current_bits = ""
    
    # Побитовый разбор
    # Первые 11 бит складываются в код, возвращающий байт 0x4B \(\rightarrow \) K
    # '1011100': 0x4b=75 ('K')
    # '11101101101': 0x6b=107 ('k') '100010': 0x33=51 ('3') '11110100011': 0xa3=163
    # '0000011000110000001000101011000001100011010011001100011100101001100011110110001000101100010001011010100010111001000101111010001100000000'
    for bit in bit_string:
        current_bits += bit
        if current_bits in lookup_table:
            byte_val = lookup_table[current_bits]
            
            # Если байт попадает в печатный ASCII диапазон
            if 32 <= byte_val <= 126:
                decoded_chars.append(chr(byte_val))
            else:
                decoded_chars.append(f"[0x{byte_val:02X}]")
                
            current_bits = ""
            
    return "".join(decoded_chars)

# --- ИСХОДНЫЕ ДАННЫЕ ВАШЕЙ СИСТЕМЫ ---
weights = {
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

start_vrtx = '0010101111011010000110110010111010010101'
# распаковка хвоста от ру34: 
# bla_bl = BLADDR(vdo.read(0xE2A2A00, 4), vdo)    # @ 07151504 1d 0105 [1D:MAP__10k400]
# ..NEXT BLOCK

# Тестируемая строка - 'kolym...?' 'laptev...?'
target_hex = "00 00 06 30 22 b0 63 4c c7 29 8f 62 2c 45 a8 b9 17 a3 00"
"""

варианты - каноническое дерево хафмана
1. для полной таблицы весов
2. для таблицы, где только буквы
3. буквы + цифры
4. буквы + цифры + символы

строку побитово сдвигать - 8 раз 15 ???
"""
from vdo.constants import *

map1 = weights_chars
map1.update(weights_digits)
map2 = map1
map2.update(weights_chars)
map3 = map2

canonical_map = generate_canonical_lookup(weights)
result_text = decode_hex_to_string(target_hex, canonical_map)

print("=== ТЕСТ РАСПАКОВКИ СТРОКИ ===")
print(f"Исходный дамп: {target_hex}")
print(f"Результат декодирования: {result_text}")
