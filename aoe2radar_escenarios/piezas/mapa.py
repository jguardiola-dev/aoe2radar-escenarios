"""Mapa: tamaño, terreno liso, recinto («ring») de agua profunda y colinas."""
from __future__ import annotations

from typing import Tuple

from AoE2ScenarioParser.datasets.terrains import TerrainId

TERRENO = TerrainId.GRASS_1
AGUA = TerrainId.WATER_DEEP


def preparar(scn, tamano: int, recinto: Tuple[int, int, int, int] | None) -> None:
    """Mapa cuadrado de {@code tamano}, todo hierba a nivel 0; con recinto, fuera de él agua profunda (no se sale a pie)."""
    mm = scn.map_manager
    mm.map_size = tamano
    for t in mm.terrain:
        t.elevation = 0
        t.layer = -1
        x, y = t.x, t.y
        dentro = recinto is None or (recinto[0] <= x <= recinto[2] and recinto[1] <= y <= recinto[3])
        t.terrain_id = TERRENO if dentro else AGUA


def colina(scn, zona: Tuple[int, int, int, int], altura: int, recinto: Tuple[int, int, int, int] | None) -> None:
    """Eleva la zona (con la pendiente alrededor que pone la propia librería, como el editor)."""
    mm = scn.map_manager
    n = mm.map_size - 1
    x1, y1, x2, y2 = zona
    if recinto is not None:                         # que la colina no se coma la orilla
        x1, y1 = max(x1, recinto[0] + 1), max(y1, recinto[1] + 1)
        x2, y2 = min(x2, recinto[2] - 1), min(y2, recinto[3] - 1)
    x1, y1, x2, y2 = max(0, x1), max(0, y1), min(n, x2), min(n, y2)
    mm.set_elevation(altura, x1, y1, x2, y2)
    if recinto is not None:                         # el agua, siempre a nivel 0
        for t in mm.terrain:
            if t.terrain_id == AGUA:
                t.elevation = 0


def elevacion(scn, x: float, y: float) -> int:
    return scn.map_manager.get_tile(int(x), int(y)).elevation
