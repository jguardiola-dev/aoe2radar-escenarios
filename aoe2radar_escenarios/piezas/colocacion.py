"""Colocación de unidades en formación. Geometría pura (sin la librería), para poder probarla aparte.

Convención: el eje x del mapa separa a los ejércitos. J1 a la izquierda (x menor) mirando a +x, J2 a la derecha
mirando a -x, centrados en y. Los grupos se colocan en el orden recibido, de la primera fila hacia atrás.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Tuple

#: Unidades por fila por defecto: la mitad del total, hasta 20 (la formación LINEA de aoe2radar).
FRENTE_MAX = 20


@dataclass(frozen=True)
class Puesto:
    unidad: int
    fondo: float      # casillas hacia atrás desde la primera fila (>= 0)
    lateral: float    # casillas a un lado del eje central (negativo / positivo)


def por_fila(total: int, pedido: int) -> int:
    if pedido > 0:
        return max(1, min(pedido, total))
    return max(1, min(FRENTE_MAX, (total + 1) // 2))


def formacion(grupos: List[Tuple[int, int]], fila: int, espaciado: float) -> List[Puesto]:
    """{@code grupos}: (unidad, cantidad) en orden de delante a atrás."""
    total = sum(c for _, c in grupos)
    n = por_fila(total, fila)
    puestos: List[Puesto] = []
    k = 0
    for unidad, cantidad in grupos:
        for _ in range(cantidad):
            f, c = divmod(k, n)
            en_fila = min(n, total - f * n)
            puestos.append(Puesto(unidad, f * espaciado, (c - (en_fila - 1) / 2.0) * espaciado))
            k += 1
    return puestos


def huella(puestos: List[Puesto]) -> Tuple[float, float]:
    """(fondo, frente) que ocupa la formación, en casillas (centro a centro + 1 de la propia unidad)."""
    if not puestos:
        return 0.0, 0.0
    fondo = max(p.fondo for p in puestos) + 1
    frente = max(p.lateral for p in puestos) - min(p.lateral for p in puestos) + 1
    return fondo, frente


@dataclass(frozen=True)
class Plano:
    """Dónde va todo en el mapa: tamaño, recinto (ring) y la posición absoluta de cada unidad."""
    tamano: int
    recinto: Tuple[int, int, int, int] | None      # x1, y1, x2, y2 (incluidos) de la zona jugable; None sin ring
    unidades: List[Tuple[int, int, float, float]]  # (jugador, unidad, x, y)
    zonas: List[Tuple[int, int, int, int]]         # rectángulo de casillas que ocupa cada jugador (para la colina)
    centros: List[Tuple[float, float]]             # centro de cada ejército


#: Aire alrededor de los ejércitos dentro del recinto, en casillas.
MARGEN = 6
#: Anchura de la banda de agua fuera del recinto.
BANDA = 4
TAMANO_MIN = 60


def planificar(formaciones: List[List[Puesto]], separacion: float, ring: bool, lado_ring: int, tamano_pedido: int) -> Plano:
    (f1, w1), (f2, w2) = huella(formaciones[0]), huella(formaciones[1])
    largo = separacion + f1 + f2 + 2 * MARGEN
    ancho = max(w1, w2) + 2 * MARGEN
    lado = int(math.ceil(max(largo, ancho, 20)))
    if ring and lado_ring > lado:
        lado = lado_ring                                  # el pedido manda si es mayor; nunca encoge por debajo de lo justo
    tamano = max(TAMANO_MIN, tamano_pedido, lado + 2 * BANDA + 2)
    c = tamano / 2.0
    recinto = None
    if ring:
        x1 = int(math.floor(c - lado / 2.0))
        recinto = (x1, x1, x1 + lado - 1, x1 + lado - 1)
    unidades, zonas, centros = [], [], []
    medio = c - (f2 - f1) / 2.0                           # el punto entre los frentes, para que el conjunto quede centrado
    for j, puestos in enumerate(formaciones):
        d = -1.0 if j == 0 else 1.0                       # J1 hacia x menor, J2 hacia x mayor
        x0 = medio + d * (separacion / 2.0 + 0.5)
        xs, ys = [], []
        for p in puestos:
            x, y = x0 + d * p.fondo, c + p.lateral
            unidades.append((j + 1, p.unidad, x, y))
            xs.append(x)
            ys.append(y)
        zonas.append((int(math.floor(min(xs))) - 2, int(math.floor(min(ys))) - 2, int(math.floor(max(xs))) + 2,
                      int(math.floor(max(ys))) + 2))
        centros.append((sum(xs) / len(xs), sum(ys) / len(ys)))
    return Plano(tamano, recinto, unidades, zonas, centros)
