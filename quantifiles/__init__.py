from __future__ import annotations

from quantifiles.main import main

from pathlib import Path

_static_reference = None


def run(data_dir: str | Path | None = None):
    _static_reference = main(data_dir)


if __name__ == "__main__":
    run()
