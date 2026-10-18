"""Punto de entrada del .exe (PyInstaller): lo mismo que `python -m aoe2radar_escenarios`."""
import sys

from aoe2radar_escenarios.__main__ import main

if __name__ == "__main__":
    sys.exit(main())
