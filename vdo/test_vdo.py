"""

Общий установочный файл для тестов 30 и 34 версии
"""

from QGIS_VDO.vdo.datatypes import VDO_FILE


fpath30 = 'c:\\DIY\\VDO\\db_src\\NAV_DB\\carindb'
vdo30 = VDO_FILE(fpath30)       # noqa: F841

fpath34bnl = 'c:\\DIY\\VDO\\db_src\\1. BNL_13_14\\carindb'
vdo34bnl = VDO_FILE(fpath34bnl)       # noqa: F841

fpath34ee = 'c:\\DIY\\VDO\\db_src\\3. EE_13_14\\carindb'
vdo34ee = VDO_FILE(fpath34ee)       # noqa: F841

fpathRu = 'c:\\DIY\\VDO\\db_src\\ru_2013\\ru\\carindb'
vdoRu = VDO_FILE(fpathRu)       # noqa: F841

fpathbmw = 'c:\\DIY\\VDO\\db_src\\bmw34-2010\\DB\\DB_0'
vdobmv = VDO_FILE(fpathbmw)       # noqa: F841
