"""Jugadores: civ, edad, recursos iniciales, población, humano/ordenador, diplomacia, cámara y visión."""
from __future__ import annotations

from typing import Iterable, Tuple

from AoE2ScenarioParser.datasets.object_support import Civilization, StartingAge
from AoE2ScenarioParser.datasets.players import PlayerId
from AoE2ScenarioParser.datasets.trigger_lists.attribute import Attribute
from AoE2ScenarioParser.datasets.trigger_lists.diplomacy_state import DiplomacyState
from AoE2ScenarioParser.datasets.trigger_lists.operation import Operation
from AoE2ScenarioParser.datasets.trigger_lists.visibility_state import VisibilityState

from ..entrada import EntradaInvalida

EDADES = {1: StartingAge.DARK_AGE, 2: StartingAge.FEUDAL_AGE, 3: StartingAge.CASTLE_AGE, 4: StartingAge.IMPERIAL_AGE}


def civilizacion(clave: str) -> Civilization:
    """La civ por su clave de aoe2techtree («Franks», «Hindustanis»…): el nombre del enumerado en mayúsculas."""
    try:
        return Civilization[clave.strip().upper().replace(" ", "_")]
    except KeyError:
        raise EntradaInvalida(f"civilización desconocida para la librería: {clave!r}") from None


def configurar(scn, civs: Iterable[Tuple[str, int]], humanos: Iterable[bool], recursos: Tuple[int, int, int, int] = (0, 0, 0, 0),
               poblacion: int = 200) -> None:
    """Un jugador por (civ, edad), en orden J1, J2…; todos enemigos de todos."""
    civs, humanos = list(civs), list(humanos)
    pm = scn.player_manager
    pm.active_players = len(civs)
    for i, ((civ, edad), humano) in enumerate(zip(civs, humanos), start=1):
        p = pm.players[i]
        c = civilizacion(civ)
        p.civilization = c
        p.architecture_set = c
        p.lock_civ = True
        p.starting_age = EDADES[edad]
        p.human = humano
        p.food, p.wood, p.gold, p.stone = recursos
        p.population_cap = poblacion
    ids = [PlayerId(i) for i in range(1, len(civs) + 1)]
    for p in ids:
        pm.players[p].set_player_diplomacy([q for q in ids if q != p], DiplomacyState.ENEMY)


def camara(scn, jugador: int, x: float, y: float) -> None:
    p = scn.player_manager.players[jugador]
    p.initial_player_view_x, p.initial_player_view_y = int(x), int(y)


def vision_total(scn, jugadores: int) -> None:
    """Trigger al empezar: mapa descubierto y cada jugador ve las unidades de los demás."""
    t = scn.trigger_manager.add_trigger("aoe2radar: vision total")
    for p in range(1, jugadores + 1):
        t.new_effect.modify_resource(quantity=1, tribute_list=Attribute.REVEAL_MAP, source_player=p, operation=Operation.SET)
        for q in range(1, jugadores + 1):
            if q != p:
                t.new_effect.set_player_visibility(source_player=p, target_player=q, visibility_state=VisibilityState.VISIBLE)
