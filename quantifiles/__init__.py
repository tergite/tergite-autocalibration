from __future__ import annotations

from pathlib import Path

from quantifiles.qml.databrowser import DataBrowser

_static_reference = None


def run(data_dir: str | Path):
    _static_reference = DataBrowser(data_dir)
