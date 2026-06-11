"""

decoding tail use huffman lookup
"""
from bitarray import bitarray
from bitarray.util import ba2int

# flake8 E501  10100011000 10100110000
"""
INPUT_STR = bitarray('1010001100010100110000 0000110000010000110000010000110000010000110000010000110000010000110000011111101101011101000101101111111000111001110110101111000001001010011110001010100011001001111010111011100110000111101101101110110001011100001011000000100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000011010001100010001010110000000000010100001101010000110101000100010100010101010001100000000000000000000000000000000')   # noqa
"""

# penzhinskaya guba    zaliv shelikhova    okhotskoe more
# 000: > a+eaeaeCNadE  aai;hak##dia+larartszhig#k!%"penzh#k!%"zaliv sheli$va#o$tskoe more#araaeaaaa (591 -> 91)
# 032: > egas#dra aai;hak##dia+larartszhi@#k!%"penzh#k!%"zaliv sheli$va#o$tskoe more#araaeaaaaaaaaa (559 -> 76) # noqa
# $ - kho
INPUT_STR_515 = bitarray('1000110000001001000001000001111000011111001110000100011110001011000010000000000111101001110111011100110001111010111101000110111100011010000011001111110101000011000001100101010011111101010011101001001011010001111110101111010000111010010111010001011111000000110110111111010100111101000111111010111101000011101001011101000101111110100001010110100111110110100000100100110011010110100110100100111110110000011110111110100100010101001111010111011100110000111101101101110110001011100001100000000010000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000')   # noqa

# # =mal. lyakhovskiy|bol. lyakhovskiy|kotel'niy|more laptevykh|vostochno sibirskoe more
# guba gusinaya
# 127: > bol. lyakhovsk#nov!$"'#kotel'n#@uba @usin!#vostochno$"skoe more#araasaaaaaaaaaaaaaaaaaaaaa (590 -> 110) # noqa
INPUT_STR_526 = bitarray('0001111000011111001110000100011110001011010011110010000111101001111100100000000001101000001110011110100100001100000100001100000111110001010111101011101011101000010101111111001000111101011100111011111111011001001111010111101000111011010111111110110110100001110100100110100010110100111011111110101110111010100110101110100111101101101000111001011111010111110001000010000100101111101010100101001011011010000101111111101101011101000101101111111000111001110110101111101001001101000100100111101011101110011000011110110110111011000101110000110000000010000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000')   # noqa

# 000: > a+a+a+a+a+a+m#stochno sibirskoe more#at eaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa#adt (468 -> 92)
# 070: > {t"?d+lAesbirskoe more#at eaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa#adt aatarieladstt (398 -> 37)
# 071: > vostochno sibirskoe more#at eaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa#adt aatarielads (397 -> 45)
# 072: > m#stochno sibirskoe more#at eaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa#adt aatarielads (396 -> 45)
INPUT_STR_54f = bitarray('0000110000010000110000010000110000010000110000010000110000010000110000011111101101011101000101101111111000111001110110101111000001001010011110001010100011001001111010111011100110000111101101101110110001011100001011000000100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000011010001100010001010110000000000010100001101010000110101000100010100010101010001100000000000000000000000000000000')   # noqa


INPUT_STR = INPUT_STR_515
bits_in_ptr = 11

lookup = {'000': 'a',   # b'\x00',       # ??????  00? @ -> a E#l. ly@khovsk
          '001': 'e',
          '0100': 's',
          '0101': 't',
          '0110': 'r',
          '0111': '#',   # '\x00',     # 01 ???????????? Сюда идеально встает буква a. UPD: а вообще похоже 00
          '10000': ' ',
          '10001': 'd',    # 02 ???????????? Сюда подходят буквы o и l (или d).
          '10010': 'g',    # 03 ???????????? Однако, по условию буква o в конце
          '10011': 'h',
          '10100': 'i',
          '10101': 'l',    # 04 ???????????? заполняется буквой c или u (с загружалась через 11, u -koteu'n)
          '10110': 'n',
          '10111': 'o'
}
# #vostochno$"skoe more#   $" -> ' sibir'?
# 127: > bol. lyakhovsk#nov!$"'#kotel'n#@uba @usin!#vostochno$"skoe more#araasaaaaaaaaaaaaaaaaaaaaa (590 -> 110)
# =mal. lyakhovskiy|bol. lyakhovskiy|kotel'niy|more laptevykh|vostochno sibirskoe more

# $ -> kh???

def decode_ascii_code() -> int:
    """
    декодирует значение символа из битового потока
    Returns:
        int: числовое значение uchar
vostochno$"skoe more#   $" -> ' sibir'?                        s
1101001001101000100100 ->              -> 110100100110100010 0100
    v       o     s    t    o       c       H    N      o    ' '    s    i      b        i    r    s      k        o    e
111110110 10111 0100 0101 10111 111100011 10011 10110 10111 10000 0100 10100 111100010 10100 0110 0100 111101011 10111 001

000: > a+eaeaeCNadE  aai;hak##dia+larartszhig#k!%"penzh#k!%"zaliv sheli$va#o$tskoe more#araaeaaaa (591 -> 91)
001: > e eeaeaeCNadE  aai;hak##dia+larartszhig#k!%"penzh#k!%"zaliv sheli$va#o$tskoe more#araaeaaa (590 -> 94)
002: > raeeaeaeCNadE  aai;hak##dia+larartszhig#k!%"penzh#k!%"zaliv sheli$va#o$tskoe more#araaeaaa (589 -> 94)


        input bitarray('1101001001101000100100111101011101110011000011110110110111011000101110000110000000010000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000')

        phrase bitarray('11000011111001110000100011110001011010011110010000111101001111100100000000001101000001110011110100100001100000100001100000111110001010111101011101011101000010101111111001000111101011100111011111111011001001111010111101000111011010111111110110110100001110100100110100010110100111011111110101110111010100110101110100111101101101000111001011111010111110001000010000100101111101010100101001011011010000101111111101101011101000101101111111000111001110110101111101001001101000100100111101011101110011000011110110110111011000101110000110000000010000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000')
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
    prev = INPUT_STR
    with open("this_log.log", "w") as f:
        f.write(f"\n")
    for _ in range(int(INPUT_STR.nbytes - 5) * 8):
        phrase = '> '
        INPUT_STR = prev[1:]
        beg_len = len(INPUT_STR)
        prev = INPUT_STR
        for offset in range(curr_offset, curr_offset + 90):
            if INPUT_STR.nbytes > 1:
                ch = decode_ascii_code()
                char = chr(ch) if ch > 31 else '+'
                phrase += char
                
                if phrase[-4:] == 'chno':
                    # отловить #vostochno$"skoe more# 
                    pass
            # print(f"{offset:04x}: {ch:02x} '{char}'")
            if offset == 0x517:
                # =mal. lyakhovskiy|bol. lyakhovskiy|kotel'niy|more laptevykh|vostochno sibirskoe more
                pass
        with open("this_log.log", "a") as f:
            f.write(f"{_:03}: {phrase} ({beg_len} -> {len(INPUT_STR)})\n")
            print(f"{_:03}: {phrase} ({beg_len} -> {len(INPUT_STR)})")
    pass

"""
print(f"{_:03}: {phrase} ({beg_len} -> {len(INPUT_STR)})")
'000':  '@',          # ??????  00?
'0111': '#',    # b'\x00',
...
068: > evostochno sibirskoe more#@t e@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#@dt @@t@rieu@d (400 -> 49)
069: > #ZQr|#e5Aesbirskoe more#@t e@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#@dt @@t@rieu@dst (399 -> 41)
070: > {t"?d|uAesbirskoe more#@t e@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#@dt @@t@rieu@dstt (398 -> 37)
071: > vostochno sibirskoe more#@t e@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#@dt @@t@rieu@ds (397 -> 45)
072: > m#stochno sibirskoe more#@t e@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#@dt @@t@rieu@ds (396 -> 45)
073: > ZQr|#e5Aesbirskoe more#@t e@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#@dt @@t@rieu@dstt (395 -> 37)
074: > 5"?d|uAesbirskoe more#@t e@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#@dt @@t@rieu@dstt@ (394 -> 34)
...
526

057: > ir@@@ Os |@|E#u. uy@khovsk#nov!$"'#koteu'n#lub@ lusin!#vostochno$"skoe more#@r@@s@@@@@@@@@ (660 -> 146)
058: > sr@@@ Os |@|E#u. uy@khovsk#nov!$"'#koteu'n#lub@ lusin!#vostochno$"skoe more#@r@@s@@@@@@@@@ (659 -> 146)
059: > hH@@r #eR@|@|E#u. uy@khovsk#nov!$"'#koteu'n#lub@ lusin!#vostochno$"skoe more#@r@@s@@@@@@@@ (658 -> 149)
060: > ed@@ei@Os |@|E#u. uy@khovsk#nov!$"'#koteu'n#lub@ lusin!#vostochno$"skoe more#@r@@s@@@@@@@@ (657 -> 149)
kotel'niy
127: > bol. lyakhovsk#nov!$"'#kotel'n#@uba @usin!#vostochno$"skoe more#araasaaaaaaaaaaaaaaaaaaaaa (590 -> 110)


"""
