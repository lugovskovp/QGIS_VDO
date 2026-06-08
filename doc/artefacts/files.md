
vdo_enums.py 1..6

vdo_paths.py 10..11

vdo_disk.py  20
	from vdo_paths 	import local_db 
	
vdo_datatypes.py  30

vdo_geotypes.py  40
	from vdo_datatypes 	import BYTESTRUCT, COORD, MULCOORD, PTR
	from vdo_enums 		import en_DRAW_TYPE, en_GEO_CATEGORY
	
vdo_block_base.py	БЕЗ ТЕСТОВ
	from vdo_datatypes 	import BLADDR, COORD, PTR, LIST, FAR_LIST

vdo_block.py  45
	from vdo_block_base import block_base
	*from vdo_paths   import local_db	
	*from vdo_carindb import carindb

vdo_map_block_base.py
	from vdo_block_base import block_base
	from vdo_datatypes import BYTESTRUCT, LIST
	from vdo_enums import en_DRAW_TYPE, en_GEO_CATEGORY
	from vdo_geotypes import MAP_AREA, GEO_CATEGORY_PROTO, GEO_SHAPE_PROTO, GEO_LINE_PROTO, VERTEX_PROTO

block_0x12.py  50
	from vdo_block_base import block_base
	from vdo_datatypes import COORD, LIST, FAR_LIST, BLADDR

block_0xEE.py 50
	from vdo_block_base import block_base

vdo_carindb.py  60
	from block_0x07 import block_0x07
	from vdo_block import get_block_class_by_type   # *
	from vdo_enums import BlockType
	from vdo_datatypes import LIST, BLADDR, FAR_LIST, COORD
	from block_0x12 import block_0x12
	from block_0xEE import block_0xEE

block_0x09.py  70
	from vdo.vdo_block_base import block_base
	from vdo.vdo_datatypes import BLADDR, LIST 

class block_0x08(block_base): 71
	from math import sqrt
	from vdo.vdo_block_base import block_base
	from vdo.vdo_datatypes import BLADDR, LIST

block_0x07.py  80
	from vdo_block_base import block_base
	from vdo_datatypes  import BYTESTRUCT, BLADDR, PTR, COORD
	from vdo_enums      import BlockType, en_POI_CATEGORY, en_GEO_COUNTRY

block_0x13   90
	from vdo.vdo_block_base import block_base
	from vdo.vdo_datatypes import LIST








PS C:\DIY\VDO\py\vdo_qgis>  c:; cd 
'c:\DIY\VDO\py\vdo_qgis'; & 
'c:\DIY\VDO\py\vdo_qgis\.venv\Scripts\python.exe' 'c:\Users\plugo\.vscode\extensions\ms-python.debugpy-2024.10.0-win32-x64\bundled\libs\debugpy\adapter/../..\debugpy\launcher' '54806' '--' 
'c:\DIY\VDO\py\vdo_qgis\blocks\vdo_block.py' 