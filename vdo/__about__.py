"""Version information for QGIS_VDO."""

__version__ = "1.0.0-dev.5"
__version_info__ = tuple(
    int(part) if part.isdigit() else part
    for part in __version__.replace("-", ".").split(".")
)
