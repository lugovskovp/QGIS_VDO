# """Сравнение bitarray и bitstream.pop()"""

# from bitarray import bitarray

# arc = bytes.fromhex('0203c0011a30000a')
# baa = bitarray(buffer=arc, endian='big')

# # ---------- Вывод битовой карты ----------
# print("=== Битовая карта байтов ===")
# for i in range(len(arc)):
#     bits = baa[i*8:(i+1)*8].to01()
#     print(f"  byte[{i:2d}] = 0x{arc[i]:02X} = {bits}")

# print()

# # ---------- bitarray[19:26] ----------
# print("=== bitarray[19:26] ===")
# shf = baa[19:26]
# print(f"  binary: {shf.to01()}")
# print(f"  int:    {int(shf.to01(), 2)}")
# print(f"  hex:    0x{int(shf.to01(), 2):02X}")

# print()

# # ---------- Эмуляция pop() ----------
# def pop_emulate(buf: bytes, start: int, qty: int):
#     """Эмуляция bitstream.pop() для одного вызова (исправленная)"""
#     byte_idx = start >> 3          # start // 8
#     bit_off = start & 7            # start % 8
    
#     n_bytes = (bit_off + qty + 7) >> 3
#     raw = buf[byte_idx : byte_idx + n_bytes]
    
#     val = int.from_bytes(raw, 'big')
#     val >>= (n_bytes * 8 - qty - bit_off)
#     val &= (1 << qty) - 1
    
#     return val, byte_idx, bit_off, n_bytes, raw

# print("=== pop(7, 19) ===")
# result, bi, bo, nb, raw = pop_emulate(arc, 19, 7)
# print(f"  byte_idx = {bi}   (19 >> 3)")
# print(f"  bit_off  = {bo}   (19 & 7)")
# print(f"  n_bytes  = {nb}   (({bo} + 7 + 7) >> 3)")
# print(f"  raw      = {raw.hex()}   (arc[{bi}:{bi+nb}])")
# print(f"  result   = {result} = 0x{result:02X}")
# print(f"  binary   = {result:07b}")

# print()

# # ---------- Сравнение для разных смещений ----------
# print("=== Сравнение bitarray vs pop() для разных смещений ===")
# print(f"  {'idx':>4s} | {'bitarray':>10s} | {'pop()':>8s} | {'raw hex':>8s} | {'совпадение'}")
# print(f"  {'':->4s}-+-{'':->10s}-+-{'':->8s}-+-{'':->8s}-+-{'':->12s}")

# for idx in range(0, 57, 1):
#     if idx + 7 > len(baa):
#         break
#     ba_val = int(baa[idx:idx+7].to01(), 2)
#     pop_val, _, _, _, raw = pop_emulate(arc, idx, 7)
#     match = "OK" if ba_val == pop_val else "MISMATCH"
#     marker = " <-- 0x60!" if pop_val == 0x60 else ""
#     print(f"  {idx:4d} | {ba_val:10d} | {pop_val:8d} | {raw.hex():>8s} | {match}{marker}")
