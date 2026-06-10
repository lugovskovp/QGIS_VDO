"""

decoding tail use huffman lookup
"""
from bitarray import bitarray
from bitarray.util import ba2int

# flake8 E501

INPUT_STR = bitarray('10100011000101001100000000110000010000110000010000110000010000110000010000110000010000110000011111101101011101000101101111111000111001110110101111000001001010011110001010100011001001111010111011100110000111101101101110110001011100001011000000100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000011010001100010001010110000000000010100001101010000110101000100010100010101010001100000000000000000000000000000000')   # noqa

INPUT_STR = bitarray('1111101101011101000101101111111000111001110110101111000001001010011110001010100011001001111010111011100110000111101101101110110001011100001011000000100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000011010001100010001010110000000000010100001101010000110101000100010100010101010001100000000000000000000000000000000')   # noqa

bits_in_ptr = 11

lookup = {'000': b'\x00',       # ??????  00?
          '001': 'e',
          '0100': 's',
          '0101': 't',
          '0110': 'r',
          '0111': 'a',     # 01 ???????????? Сюда идеально встает буква a.
          '10000': ' ',
          '10001': 'd',    # 02 ???????????? Сюда подходят буквы o и l (или d).
          '10010': 'l',    # 03 ???????????? Однако, по условию буква o в конце
          '10011': 'h',
          '10100': 'i',
          '10101': 'u',    # 04 ???????????? заполняется буквой c или u (с загружалась через 11)
          '10110': 'n',
          '10111': 'o'
}


def decode_ascii_code() -> int:
    """
    декодирует значение символа из битового потока
    Returns:
        int: числовое значение uchar
    """
    global INPUT_STR
    prefix = INPUT_STR[:2]
    INPUT_STR = INPUT_STR[2:]
    if prefix.to01() == '11':
        # just load
        val = ba2int(INPUT_STR[:7])
        INPUT_STR = INPUT_STR[7:]
        return val
    #
    if prefix.to01() == '00':
        #
        prefix += INPUT_STR[:1]
        INPUT_STR = INPUT_STR[1:]
    elif prefix.to01() == '01':
        #
        prefix += INPUT_STR[:2]
        INPUT_STR = INPUT_STR[2:]
    else:   # elif prefix.to01() == '10':
        #
        prefix += INPUT_STR[:3]
        INPUT_STR = INPUT_STR[3:]
    val = lookup[prefix.to01()]
    val = ord(val)
    return val


if __name__ == "__main__":

    # первые 2 значения - начальный и завершающий оффсет для str
    # offset_str_start = ba2int(INPUT_STR[:bits_in_ptr])
    # INPUT_STR = INPUT_STR[bits_in_ptr:]
    # offset_str_end = ba2int(INPUT_STR[:bits_in_ptr])
    # INPUT_STR = INPUT_STR[bits_in_ptr:]
    # char_cnt = offset_str_end - offset_str_start
    curr_offset = 0x050C
    curr_offset = 0x0518
    # print(f"from 0x{offset_str_start:x} to 0x{offset_str_end:x} len: {char_cnt} curr: {curr_offset:x}")
    for offset in range(curr_offset, curr_offset + 50):
        ch = decode_ascii_code()
        char = chr(ch) if ch > 31 else ''
        print(f"{offset:04x}: {ch:02x} '{char}'")
        if offset == 0x517:
            pass
    pass