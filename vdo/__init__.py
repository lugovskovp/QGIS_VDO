# flake8: noqa  Отключить предупреждение неиспользованного импорта

from QGIS_VDO.vdo.datatypes import VDO_FILE, BLADDR, PTR, LIST, FAR_LIST, CH_IDX, BLSTART  # noqa: F401, E501 (Ignores only "unused import")
# from QGIS_VDO.vdo.CollapsibleGroupBox import CollapsibleGroupBox, CollapsibleBox  # noqa: F401, E501 (Ignores only "unused import")# noqa: F401, E501 (Ignores only "unused import")
from QGIS_VDO.vdo.geotypes import COORD # noqa
from QGIS_VDO.vdo.consts import (
    CRS_NAME,
    CRS_PROJECTION_STRING,
)
from QGIS_VDO.vdo.consts_layers import (
    NAME_LAYER_GLOBAL_BOUNDS,
    NAME_LAYER_ALMANACS,
    NAME_LAYER_POI,
    NAME_LAYER_SHAPES,
    NAME_LAYER_LINES,
    PEN_STYLES,
    FILL_STYLES,
    LAYERS_PROPERTY
    )  # noqa
