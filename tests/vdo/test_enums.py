import pytest   # type: ignore # noqa
import os

from qgis.core import QgsApplication

from QGIS_VDO.vdo import (
    LAYERS_PROPERTY,
    NAME_LAYER_POI,
    NAME_LAYER_GLOBAL_BOUNDS,
    NAME_LAYER_ALMANACS,
    NAME_LAYER_SHAPES,
    NAME_LAYER_LINES,
)
from QGIS_VDO.vdo.enums import en_POI_CAT


expected_categories = {item.name: item.value for item in en_POI_CAT}
registry = {obj['name']: obj for obj in LAYERS_PROPERTY}
layer = registry.get(NAME_LAYER_POI)
styles = {obj['name']: obj for obj in layer.get('styles')}


def test_LAYERS_PROPERTY_consists_all_layers():
    expected_names = [
        NAME_LAYER_GLOBAL_BOUNDS,
        NAME_LAYER_ALMANACS,
        NAME_LAYER_POI,
        NAME_LAYER_SHAPES,
        NAME_LAYER_LINES,
    ]
    set_layers = {lay['name'] for lay in LAYERS_PROPERTY}
    
    assert set_layers == set(expected_names)


@pytest.mark.parametrize("cat_value", en_POI_CAT)
def test_en_POI_CAT_all_cat_has_icons(cat_value):
    st = styles.get(cat_value.name)

    assert st is not None    # все en_POI_CAT имеют стиль

    svg_path = st.get('style').get('svg_path')
    assert svg_path is not None    # все path - есть

    for base_dir in QgsApplication.svgPaths():      # pragma: no cover
        potential_path = os.path.join(base_dir, svg_path)
        if os.path.exists(potential_path):
            full_svg_path = potential_path
            break
    assert os.path.isfile(full_svg_path)  # файлы svg физически существуют
