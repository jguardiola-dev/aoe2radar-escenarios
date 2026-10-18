"""Mejoras: tecnologías investigadas al empezar, con el efecto «Research Technology» (forzado: no hace falta edificio)."""
from __future__ import annotations

from typing import Iterable


def investigar(scn, jugador: int, tecnologias: Iterable[int]) -> None:
    techs = list(dict.fromkeys(tecnologias))   # sin repetir, en el orden recibido
    if not techs:
        return
    t = scn.trigger_manager.add_trigger(f"aoe2radar: mejoras J{jugador}")
    for tech in techs:
        t.new_effect.research_technology(source_player=jugador, technology=tech, force_research_technology=1)
