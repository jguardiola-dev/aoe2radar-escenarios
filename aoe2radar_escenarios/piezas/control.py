"""Órdenes al empezar: postura agresiva y «atacar moviéndose» hacia el ejército contrario."""
from __future__ import annotations

from typing import Iterable, Tuple

from AoE2ScenarioParser.datasets.trigger_lists.attack_stance import AttackStance


def al_ataque(scn, tamano: int, espera_s: int, ordenes: Iterable[Tuple[int, float, float]]) -> None:
    """{@code ordenes}: (jugador, x, y) destino. Todos los jugadores con unidades quedan en postura agresiva."""
    ordenes = list(ordenes)
    t = scn.trigger_manager.add_trigger("aoe2radar: al ataque")
    if espera_s > 0:
        t.new_condition.timer(timer=espera_s)
    n = tamano - 1
    for p in (1, 2):
        t.new_effect.change_object_stance(source_player=p, area_x1=0, area_y1=0, area_x2=n, area_y2=n,
                                          attack_stance=AttackStance.AGGRESSIVE_STANCE)
    for p, x, y in ordenes:
        t.new_effect.attack_move(source_player=p, area_x1=0, area_y1=0, area_x2=n, area_y2=n, location_x=int(x), location_y=int(y))
