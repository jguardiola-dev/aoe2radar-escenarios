"""Medición: un script XS que vigila la pelea y, al acabar, escribe en el chat quién ganó, los supervivientes y el tiempo.

Por qué XS y no solo triggers: el chat de un trigger no puede escribir números calculados; ``xsChatData`` sí. Cada
segundo cuenta las unidades vivas de cada jugador (las de cada tipo colocado y, por si una mejora cambiara el tipo, la
población militar); cuando un lado llega a cero, escribe el resultado una vez y se apaga. El tiempo se cuenta desde la orden de ataque.
"""
from __future__ import annotations

import re
from typing import Dict, List, Tuple

TEXTOS: Dict[str, Dict[str, str]] = {
    "es": {"gana": "aoe2radar: gana J%d", "empate": "aoe2radar: empate, no queda nadie", "tiempo": "Tiempo de pelea: %d s",
           "vivos": "Supervivientes de J%d", "total": "  total: %d", "unidad": "  {nombre}: %d"},
    "en": {"gana": "aoe2radar: P%d wins", "empate": "aoe2radar: draw, nobody is left", "tiempo": "Fight time: %d s",
           "vivos": "P%d survivors", "total": "  total: %d", "unidad": "  {nombre}: %d"},
}

#: Atributo de jugador «Military Population».
POBLACION_MILITAR = 40
NOMBRE_REGLA = "aoe2radarMedir"


def _cadena(s: str) -> str:
    """Texto seguro dentro de una cadena XS (sin comillas, barras ni saltos; sin '%' que no sea nuestro)."""
    return re.sub(r'["\\%\r\n\t]', "", s)


def script(grupos: List[List[Tuple[int, str]]], espera_s: int, idioma: str) -> str:
    """{@code grupos[j]}: (unidad, nombre) de cada tipo colocado para el jugador j+1."""
    tx = TEXTOS.get(idioma, TEXTOS["es"])
    lineas = [
        "// aoe2radar-escenarios: medición de la batalla (GPL-3.0)",
        f"rule {NOMBRE_REGLA}",
        "    active",
        "    minInterval 1",
        "{",
        f"    int t = xsGetGameTime() - {int(espera_s)};",
        "    if (t < 2) { return; }",
    ]
    for j, gs in enumerate(grupos, start=1):
        suma = " + ".join(f"xsGetObjectCount({j}, {u})" for u, _ in gs) or "0"
        lineas += [
            f"    int vivos{j} = {suma};",
            f"    float mil{j} = xsPlayerAttribute({j}, {POBLACION_MILITAR});",
        ]
    lineas += [
        "    if ((vivos1 > 0 || mil1 > 0.0) && (vivos2 > 0 || mil2 > 0.0)) { return; }",
        f'    if (vivos1 > 0 || mil1 > 0.0) {{ xsChatData("{_cadena(tx["gana"])}", 1); }}',
        f'    else if (vivos2 > 0 || mil2 > 0.0) {{ xsChatData("{_cadena(tx["gana"])}", 2); }}',
        f'    else {{ xsChatData("{_cadena(tx["empate"])}", 0); }}',
        f'    xsChatData("{_cadena(tx["tiempo"])}", t);',
    ]
    for j, gs in enumerate(grupos, start=1):
        lineas += [f"    if (vivos{j} > 0) {{",
                   f'        xsChatData("{_cadena(tx["vivos"])}", {j});',
                   f'        xsChatData("{_cadena(tx["total"])}", vivos{j});']
        for u, nombre in gs:
            etiqueta = _cadena(tx["unidad"].replace("%d", "")).format(nombre=_cadena(nombre) or f"#{u}")
            lineas.append(f'        xsChatData("{etiqueta}%d", xsGetObjectCount({j}, {u}));')
        lineas.append("    }")
    lineas += ["    xsDisableSelf();", "}", ""]
    return "\n".join(lineas)


def anadir(scn, xs: str) -> None:
    scn.xs_manager.add_script(xs_string=xs)
