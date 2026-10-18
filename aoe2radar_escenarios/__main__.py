"""CLI: ``python -m aoe2radar_escenarios entrada.json salida.aoe2scenario [--resultado resultado.json]``.

Códigos de salida: 0 bien; 2 entrada inválida (el JSON no cumple el esquema); 3 error al generar o escribir.
Con ``--resultado``, además escribe un JSON {"ok": true|false, "error": "...", ...}: quien llama sin consola
(pythonw.exe o el .exe sin ventana) lee ese archivo en vez de la salida estándar.
"""
from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path

from . import VERSION_ESQUEMA, __version__


def _decir(texto: str, error: bool = False) -> None:
    flujo = sys.stderr if error else sys.stdout
    if flujo is not None:                       # pythonw / exe sin ventana: no hay consola
        try:
            print(texto, file=flujo)
        except OSError:
            pass


def _resultado(ruta: str | None, datos: dict) -> None:
    if ruta:
        Path(ruta).write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="aoe2radar-escenarios",
                                 description="Genera un escenario de AoE2 DE (.aoe2scenario) a partir de un JSON (esquema v1).")
    ap.add_argument("--version", action="version",
                    version=f"aoe2radar-escenarios {__version__} (esquema {VERSION_ESQUEMA}; AoE2ScenarioParser {_version_lib()})")
    ap.add_argument("entrada", help="JSON de entrada (ver docs/esquema-v1.md)")
    ap.add_argument("salida", help="ruta del .aoe2scenario a escribir")
    ap.add_argument("--resultado", help="escribe aquí un JSON con el resultado (ok / error)")
    a = ap.parse_args(argv)

    from . import entrada, generador
    try:
        detalle = generador.generar(generador.leer_json(Path(a.entrada)), Path(a.salida))
    except entrada.EntradaInvalida as e:
        _decir(f"entrada inválida: {e}", error=True)
        _resultado(a.resultado, {"ok": False, "codigo": 2, "error": f"entrada inválida: {e}"})
        return 2
    except Exception as e:  # noqa: BLE001 - cualquier fallo de la librería o del disco se informa igual
        _decir(traceback.format_exc(), error=True)
        _resultado(a.resultado, {"ok": False, "codigo": 3, "error": f"{type(e).__name__}: {e}"})
        return 3
    _decir(f"escenario escrito: {Path(a.salida).resolve()}")
    _resultado(a.resultado, {"ok": True, "salida": str(Path(a.salida).resolve()), **detalle})
    return 0


def _version_lib() -> str:
    try:
        from AoE2ScenarioParser.version import __version__ as v
        return v
    except Exception:  # noqa: BLE001
        return "?"


if __name__ == "__main__":
    sys.exit(main())
