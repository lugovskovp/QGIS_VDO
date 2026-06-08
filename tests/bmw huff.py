import binascii

def parse_carin_slice(hex_string, start_bytes, end_bytes):
    # 1. Очищаем HEX от пробелов и переносов строк
    hex_clean = "".join(c for c in hex_string if c.isalnum())
    
    try:
        binary_data = binascii.unhexlify(hex_clean)
    except Exception as e:
        print(f"Ошибка декодирования HEX: {e}")
        return {}
    
    # 2. Делаем срез строго по указанным смещениям байт
    # Ограничиваем диапазон безопасными границами длины файла
    slice_data = binary_data[start_bytes:min(end_bytes, len(binary_data))]
    
    result_table = {}
    i = 0
    
    # 3. Шагаем блоками по 4 байта (uint16_key + uint16_value)
    while i <= len(slice_data) - 4:
        key_id = int.from_bytes(slice_data[i:i+2], byteorder='big')
        value_weight = int.from_bytes(slice_data[i+2:i+4], byteorder='big')
        
        # Фильтр: Ключ должен укладываться в один байт (0x00 - 0xFF)
        if 0 <= key_id <= 0xFF:
            # Для удобства визуального контроля выводим ASCII-символ, если он печатный
            if 32 <= key_id <= 126:
                key_title = f"0x{key_id:02X} ('{chr(key_id)}')"
            else:
                key_title = f"0x{key_id:02X}"
                
            result_table[key_title] = value_weight
            
        i += 4
        
    return result_table

# --- ВАШ ВХОДНОЙ ДАМП ДАННЫХ ---
raw_hex_data = """
00 00 00 01 00 12 00 00 00 60 00 01 00 00 07 01 00 0c 00 11 00 00 02 01 00 01 00 22 
00 00 00 0c 00 01 00 60 00 68 00 1f 00 a6 00 5d 02 00 00 01 00 00 00 00 06 e6 79 aa 
0b b1 de 1f 28 c7 b2 b8 17 56 9f 41 00 00 07 01 00 0c 00 11 02 1c 00 19 10 7a cf d8 
0d ab 93 b6 28 c7 b2 b8 17 29 94 70 00 00 03 04 00 01 00 00 00 00 00 01 00 02 00 03 
00 04 00 06 00 07 00 08 00 09 00 0a 00 0b 00 0c 00 0d 00 0e 00 0f 00 10 00 11 00 12 
00 13 00 14 00 15 00 16 00 17 00 18 00 19 00 1a 00 1b 00 1c 00 1d 00 1e 00 00 00 01 
00 0c 00 02 00 10 00 03 00 08 00 04 00 1c 00 05 00 08 00 06 00 10 00 07 00 08 00 08 
00 20 00 09 00 1a 00 0a 00 06 00 0b 00 74 00 0c 00 06 00 0d 00 04 00 0e 00 30 00 0f 
00 08 00 10 00 08 00 11 00 3c 00 12 00 04 00 13 00 06 00 14 00 08 00 15 00 06 00 16 
00 06 00 17 01 74 00 18 00 1c 00 19 01 60 00 1a 00 0c 00 1b 00 60 00 1c 00 54 00 1d 
00 04 00 1e 00 08 00 1f 00 18 00 20 00 38 00 21 00 10 00 22 00 04 00 23 00 04 00 24 
00 04 00 25 00 14 00 26 00 04 00 27 00 08 00 28 00 0c 00 29 00 0c 00 2a 00 04 00 2b 
00 30 00 2c 00 08 00 2d 00 08 00 2e 00 20 00 2f 00 28 00 30 00 0c 00 31 00 08 00 32 
00 1c 00 33 00 20 00 34 00 10 00 35 00 08 00 36 00 10 00 37 00 0a 00 38 00 04 00 39 
00 04 00 3a 00 14 00 3b 00 04 00 3c 00 10 00 3d 00 34 00 3e 00 14 00 3f 00 18 00 40 
00 0a 00 41 00 06 00 42 00 18 00 43 00 1c 00 44 00 04 00 45 00 10 00 46 00 64 00 47 
00 10 00 48 00 04 00 49 00 04 00 4a 00 08 00 4b 00 14 00 4c 00 08 00 4d 00 0c 00 4e 
00 1c 00 4f 00 04 00 50 00 10 00 51 00 28 00 52 00 10 00 53 00 04 00 54 00 04 00 55 
00 08 00 56 00 18 00 57 00 0c 00 58 00 04 00 59 00 04 00 5a 00 02
"""

# Парсим строго между смещениями 0xA6 и 0x21A
huffman_table = parse_carin_slice(raw_hex_data, start_bytes=0xA6, end_bytes=0x21A)

# Выводим собранный результат
print(f"Всего валидных токенов собрано: {len(huffman_table)}\n")
for item_key, item_value in huffman_table.items():
    print(f"{item_key} => Длина/Вес: {item_value}")