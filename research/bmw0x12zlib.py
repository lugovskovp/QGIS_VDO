import zlib

# Извлекаем бинарный кусок, начиная с 78 DA
# zlib_data = bytes.fromhex(
#     "78daed514d4ac43014ceb8100c88823b71f170a50b3b4d3b323f0b41bc801bd7256dde68"
#     "9834e924e9880bafe0153c82c7f008ee3c8ba963eb0c0eee053f0879f0bef77d5f5ec83e"
#     "e991a3707ae4988cc80eb9247bdbcfb3d7dd8bb7a783f7ab9b43c797b67bbd4508d10614"
#     "cf51358540575859796934a12c02d0bcc4096c82ad5d7677mg693fcf4c852a8bc7f34196"
#     "c42c8ed3f8bc4a584493305f18ed51fbc9c67927399c2cef539a06b6c172b31934167410"
#     "28aeae2a25d1fee469bef038a7c3a5eb02bc310a16685d784cc7aeac115dca7e13bec94d"
#     "47ed90d455ed612a15ba6f073afe6a2f`c54070bfba9456ee8c0de30165710422078b0a"
#     "b943d07599afa44d0321ec7545cc62c9edac73bb15d336342411a3f02bac707d5f162176"
#     "a16a8182b2644d3c7f58db93c89b1e65e92749c8e69fb9025e14e8ba0453ae1c524afef1"
#     "b7f001133093fe"
# )

from vdo.blocks import block_0x12       # noqa
from vdo.enums import BlockType       # noqa
from vdo.datatypes import VDO_FILE, UINT_struct, BLADDR

fpathbmw = 'c:\\DIY\\VDO\\db_src\\bmw34-2010\\DB\\DB_0'
vdobmv = VDO_FILE(fpathbmw)       # noqa: F841

block_0x12 = vdobmv.get_block(0)

try:
    decompressed = zlib.decompress(zlib_data)
    print("Успешно распаковано! Длина:", len(decompressed))
    print("Данные в HEX:", decompressed.hex())
    print("Данные в Тексте:", decompressed)
except Exception as e:
    print("Ошибка распаковки:", e)