"""Registro de tipos de escenario. Cada tipo es una función ``generar(scn, raiz) -> dict`` que recibe el escenario base
(vacío, de la librería) y el JSON ya parseado, y lo rellena con las piezas de ``aoe2radar_escenarios.piezas``.

Para añadir un tipo nuevo: un módulo en este paquete, su validación en ``entrada.py`` y una línea en ``TIPOS``.
"""
from . import batalla

TIPOS = {
    "batalla": batalla.generar,
}
