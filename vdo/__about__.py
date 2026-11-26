"""Version information for QGIS_VDO."""

__version__ = "1.2.0-dev.3"
__version_info__ = tuple(
    int(part) if part.isdigit() else part
    for part in __version__.replace("-", ".").split(".")
)
