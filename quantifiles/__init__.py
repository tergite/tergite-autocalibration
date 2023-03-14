from __future__ import annotations

from quantifiles.main import main

from pathlib import Path

__all__ = ["quantifiles"]

_static_reference = None


def quantifiles(data_dir: str | Path | None = None):
    global _static_reference

    if _static_reference is None:
        _static_reference = main(data_dir)

    return _static_reference


if __name__ == "__main__":
    quantifiles()
