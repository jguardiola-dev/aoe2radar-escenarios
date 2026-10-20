"""Textos dentro del escenario: el objetivo (pestaña de mensajes del editor y panel de objetivos), un aviso al empezar,
quién gana al acabar y un recordatorio si la dificultad no es «Difícil».

Por qué así:
- La dificultad de la IA NO se guarda en el escenario (el formato no tiene ese campo): se elige al lanzarlo. Lo que sí se
  puede es leerla desde XS (``xsGetDifficulty``) y avisar en el chat si no es «Difícil».
- «Gana J1/J2» va con triggers puros (no depende de la medición): cuando un jugador se queda sin unidades militares y el
  otro aún tiene, sale el aviso en pantalla. El escenario NO se cierra (victoria personalizada sin condiciones).
"""
from __future__ import annotations

from AoE2ScenarioParser.datasets.trigger_lists.object_type import ObjectType

TEXTOS = {
    "es": {
        "objetivo": ("Batalla de aoe2radar.\n"
                     "Tú eres J1 (azul). J2 (rojo) es el ordenador.\n"
                     "{orden}\n"
                     "Gana quien deje al otro sin unidades militares; al acabar, un aviso en pantalla dice quién ganó.{medir}\n"
                     "Para que la IA juegue en serio, elige la dificultad «Difícil» al lanzar el escenario "
                     "(el archivo no puede fijarla).\n"
                     "El escenario no se cierra solo: sal con el menú cuando quieras."),
        "orden_p2": "A los {s} s, J2 ataca hacia ti en postura agresiva; tus unidades también están en agresiva.",
        "orden_ambos": "A los {s} s, los dos ejércitos avanzan solos y pelean en postura agresiva: no hace falta tocar nada.",
        "orden_nadie": "Nadie avanza solo: las unidades están en postura agresiva y pelean al acercarse.",
        "medir": "\nEl chat escribirá además el tiempo de pelea y los supervivientes por tipo.",
        "inicio": "aoe2radar: tú eres J1 (azul). {orden}",
        "gana1": "aoe2radar: gana J1 (azul). Queda J1 en pie.",
        "gana2": "aoe2radar: gana J2 (rojo). Queda J2 en pie.",
        "empate": "aoe2radar: empate, no queda nadie.",
        "dificultad": "aoe2radar: la dificultad no es Difícil. Para probar contra la IA en serio, vuelve a lanzarlo en Difícil.",
    },
    "en": {
        "objetivo": ("aoe2radar battle.\n"
                     "You are P1 (blue). P2 (red) is the computer.\n"
                     "{orden}\n"
                     "Whoever leaves the other without military units wins; when it ends, an on-screen notice says who won.{medir}\n"
                     "For the AI to play seriously, pick the “Hard” difficulty when you launch the scenario "
                     "(the file cannot set it).\n"
                     "The scenario does not close by itself: leave from the menu whenever you want."),
        "orden_p2": "After {s} s, P2 attacks you in aggressive stance; your units are aggressive too.",
        "orden_ambos": "After {s} s, both armies advance on their own and fight in aggressive stance: no need to touch anything.",
        "orden_nadie": "Nobody advances on their own: units are in aggressive stance and fight when they get close.",
        "medir": "\nThe chat will also write the fight time and the survivors by type.",
        "inicio": "aoe2radar: you are P1 (blue). {orden}",
        "gana1": "aoe2radar: P1 (blue) wins. P1 is still standing.",
        "gana2": "aoe2radar: P2 (red) wins. P2 is still standing.",
        "empate": "aoe2radar: draw, nobody is left.",
        "dificultad": "aoe2radar: the difficulty is not Hard. To test against the AI seriously, launch it again on Hard.",
    },
}

#: Segundos en pantalla del aviso de inicio y del resultado.
SEGUNDOS_INICIO = 15
SEGUNDOS_FIN = 120
NOMBRE_REGLA_DIFICULTAD = "aoe2radarDificultad"


def _tx(idioma: str) -> dict:
    return TEXTOS.get(idioma, TEXTOS["es"])


def orden(idioma: str, espera_s: int, p1_ataca: bool, p2_ataca: bool) -> str:
    tx = _tx(idioma)
    clave = "orden_ambos" if p1_ataca and p2_ataca else "orden_p2" if p2_ataca else "orden_nadie"
    return tx[clave].format(s=int(espera_s))


def objetivo(idioma: str, espera_s: int, p1_ataca: bool, p2_ataca: bool, medir: bool) -> str:
    tx = _tx(idioma)
    return tx["objetivo"].format(orden=orden(idioma, espera_s, p1_ataca, p2_ataca), medir=tx["medir"] if medir else "")


def script_dificultad(idioma: str) -> str:
    """Regla XS que mira la dificultad a los 2 s y, si no es «Difícil», lo dice en el chat (una vez)."""
    texto = _tx(idioma)["dificultad"].replace('"', "").replace("\\", "").replace("%", "")
    return "\n".join([
        "// aoe2radar-escenarios: aviso de dificultad (GPL-3.0)",
        f"rule {NOMBRE_REGLA_DIFICULTAD}",
        "    active",
        "    minInterval 2",
        "{",
        "    if (xsGetGameTime() < 2) { return; }",
        "    if (xsGetDifficulty() != cDifficultyHard) {",
        f'        xsChatData("{texto}", 0);',
        "    }",
        "    xsDisableSelf();",
        "}",
        "",
    ])


def anadir(scn, idioma: str, espera_s: int, p1_ataca: bool, p2_ataca: bool, medir: bool) -> None:
    tx = _tx(idioma)
    scn.message_manager.instructions = objetivo(idioma, espera_s, p1_ataca, p2_ataca, medir)

    inicio = scn.trigger_manager.add_trigger("aoe2radar: aviso de inicio")
    inicio.new_effect.display_instructions(source_player=1, message=tx["inicio"].format(orden=orden(idioma, espera_s, p1_ataca, p2_ataca)),
                                           display_time=SEGUNDOS_INICIO, instruction_panel_position=0)

    militar = ObjectType.MILITARY
    for ganador, perdedor, clave in ((1, 2, "gana1"), (2, 1, "gana2")):
        t = scn.trigger_manager.add_trigger(f"aoe2radar: gana J{ganador}")
        t.new_condition.own_fewer_objects(quantity=0, source_player=perdedor, object_type=militar)
        t.new_condition.own_objects(quantity=1, source_player=ganador, object_type=militar)
        t.new_effect.display_instructions(source_player=1, message=tx[clave], display_time=SEGUNDOS_FIN, instruction_panel_position=0)
    t = scn.trigger_manager.add_trigger("aoe2radar: empate")
    for p in (1, 2):
        t.new_condition.own_fewer_objects(quantity=0, source_player=p, object_type=militar)
    t.new_effect.display_instructions(source_player=1, message=tx["empate"], display_time=SEGUNDOS_FIN, instruction_panel_position=0)

    scn.xs_manager.add_script(xs_string=script_dificultad(idioma))
