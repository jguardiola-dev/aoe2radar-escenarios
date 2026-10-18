"""Lectura y validación del JSON de entrada (esquema v1, ver docs/esquema-v1.md).

Solo valida la FORMA (tipos, rangos). Nada de conocimiento del juego: los ids de unidad y de tecnología llegan ya
elegidos por quien llama (aoe2radar los saca del tech tree), y los grupos ya vienen ordenados de delante a atrás.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from . import VERSION_ESQUEMA


class EntradaInvalida(ValueError):
    """El JSON no cumple el esquema: el mensaje dice qué campo y por qué."""


# ------------------------------------------------------------------------------------------------ modelo

@dataclass
class Grupo:
    unidad: int
    cantidad: int
    nombre: str = ""


@dataclass
class Jugador:
    civ: str
    edad: int
    tecnologias: List[int] = field(default_factory=list)
    grupos: List[Grupo] = field(default_factory=list)
    por_fila: int = 0          # 0 = la mitad de las unidades (hasta 20), como la formación LINEA de aoe2radar
    espaciado: float = 1.0     # casillas entre centros de unidades vecinas

    @property
    def total(self) -> int:
        return sum(g.cantidad for g in self.grupos)


@dataclass
class Ring:
    activo: bool = True
    lado: int = 0              # casillas de lado del recinto; 0 = el justo para que quepan (con margen)


@dataclass
class Colina:
    bajo: int = 0              # 0 ninguna, 1 bajo el jugador 1, 2 bajo el jugador 2
    altura: int = 2            # niveles de elevación (1-7)


@dataclass
class Control:
    p2_ataca: bool = True      # al empezar, las unidades de J2 avanzan atacando hacia J1
    p1_ataca: bool = False     # lo mismo para J1 (útil para medir sin tocar nada)
    espera_s: int = 3          # segundos antes de la orden de ataque


@dataclass
class Batalla:
    nombre: str
    idioma: str
    jugadores: List[Jugador]
    separacion: float
    ring: Ring
    colina: Colina
    control: Control
    medir: bool
    tamano_mapa: int = 0       # 0 = automático (mínimo 60)


# ------------------------------------------------------------------------------------------------ validación

def _obj(v: Any, campo: str) -> Dict[str, Any]:
    if not isinstance(v, dict):
        raise EntradaInvalida(f"'{campo}' debe ser un objeto")
    return v


def _int(m: Dict[str, Any], k: str, campo: str, defecto: Optional[int] = None, minimo: Optional[int] = None,
         maximo: Optional[int] = None) -> int:
    v = m.get(k, defecto)
    if v is None:
        raise EntradaInvalida(f"falta '{campo}.{k}'")
    if isinstance(v, bool) or not isinstance(v, (int, float)) or int(v) != v:
        raise EntradaInvalida(f"'{campo}.{k}' debe ser un entero: {v!r}")
    v = int(v)
    if minimo is not None and v < minimo or maximo is not None and v > maximo:
        raise EntradaInvalida(f"'{campo}.{k}' fuera de rango [{minimo}, {maximo}]: {v}")
    return v


def _num(m: Dict[str, Any], k: str, campo: str, defecto: float, minimo: float, maximo: float) -> float:
    v = m.get(k, defecto)
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise EntradaInvalida(f"'{campo}.{k}' debe ser un número: {v!r}")
    if not (minimo <= v <= maximo):
        raise EntradaInvalida(f"'{campo}.{k}' fuera de rango [{minimo}, {maximo}]: {v}")
    return float(v)


def _bool(m: Dict[str, Any], k: str, campo: str, defecto: bool) -> bool:
    v = m.get(k, defecto)
    if not isinstance(v, bool):
        raise EntradaInvalida(f"'{campo}.{k}' debe ser true o false: {v!r}")
    return v


def _str(m: Dict[str, Any], k: str, campo: str, defecto: Optional[str] = None) -> str:
    v = m.get(k, defecto)
    if not isinstance(v, str) or (defecto is None and not v.strip()):
        raise EntradaInvalida(f"'{campo}.{k}' debe ser un texto")
    return v


def cabecera(raiz: Any) -> str:
    """Comprueba versión y devuelve el tipo de escenario pedido."""
    m = _obj(raiz, "raíz")
    version = m.get("version")
    if version != VERSION_ESQUEMA:
        raise EntradaInvalida(f"versión de esquema no admitida: {version!r} (esta herramienta entiende la {VERSION_ESQUEMA})")
    return _str(m, "tipo", "raíz")


def jugador(m: Dict[str, Any], campo: str) -> Jugador:
    grupos = []
    lista = m.get("grupos")
    if not isinstance(lista, list) or not lista:
        raise EntradaInvalida(f"'{campo}.grupos' debe ser una lista con al menos un grupo")
    for i, g in enumerate(lista):
        c = f"{campo}.grupos[{i}]"
        g = _obj(g, c)
        grupos.append(Grupo(unidad=_int(g, "unidad", c, minimo=0), cantidad=_int(g, "cantidad", c, minimo=1, maximo=200),
                            nombre=_str(g, "nombre", c, "")))
    techs = m.get("tecnologias", [])
    if not isinstance(techs, list) or any(isinstance(t, bool) or not isinstance(t, int) or t < 0 for t in techs):
        raise EntradaInvalida(f"'{campo}.tecnologias' debe ser una lista de ids (enteros >= 0)")
    j = Jugador(civ=_str(m, "civ", campo), edad=_int(m, "edad", campo, minimo=1, maximo=4), tecnologias=list(techs),
                grupos=grupos, por_fila=_int(m, "por_fila", campo, 0, 0, 200),
                espaciado=_num(m, "espaciado", campo, 1.0, 0.3, 4.0))
    if j.total > 200:
        raise EntradaInvalida(f"'{campo}': como mucho 200 unidades por jugador ({j.total})")
    return j


def batalla(raiz: Dict[str, Any]) -> Batalla:
    m = _obj(raiz, "raíz")
    js = m.get("jugadores")
    if not isinstance(js, list) or len(js) != 2:
        raise EntradaInvalida("'jugadores' debe tener exactamente dos jugadores (J1 y J2)")
    ring = _obj(m.get("ring", {}), "ring")
    colina = _obj(m.get("colina", {}), "colina")
    control = _obj(m.get("control", {}), "control")
    mapa = _obj(m.get("mapa", {}), "mapa")
    idioma = _str(m, "idioma", "raíz", "es")
    return Batalla(
        nombre=_str(m, "nombre", "raíz", ""),
        idioma="en" if idioma == "en" else "es",
        jugadores=[jugador(_obj(js[0], "jugadores[0]"), "jugadores[0]"), jugador(_obj(js[1], "jugadores[1]"), "jugadores[1]")],
        separacion=_num(m, "separacion", "raíz", 8, 0, 60),
        ring=Ring(activo=_bool(ring, "activo", "ring", True), lado=_int(ring, "lado", "ring", 0, 0, 200)),
        colina=Colina(bajo=_int(colina, "bajo", "colina", 0, 0, 2), altura=_int(colina, "altura", "colina", 2, 1, 7)),
        control=Control(p2_ataca=_bool(control, "p2_ataca", "control", True), p1_ataca=_bool(control, "p1_ataca", "control", False),
                        espera_s=_int(control, "espera_s", "control", 3, 0, 60)),
        medir=_bool(m, "medir", "raíz", False),
        tamano_mapa=_int(mapa, "tamano", "mapa", 0, 0, 240),
    )
