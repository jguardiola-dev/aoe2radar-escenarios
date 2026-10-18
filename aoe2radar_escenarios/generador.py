"""Del JSON al .aoe2scenario: carga el escenario base de la librería, despacha al tipo pedido y escribe el archivo."""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict

from AoE2ScenarioParser import settings

from . import __version__, entrada
from .tipos import TIPOS

# La librería escribe su progreso en la consola y lanza xs-check al escribir: aquí no queremos ninguna de las dos cosas
# (la herramienta corre sin ventana y su única salida son archivos). Los tests validan el XS aparte.
settings.PRINT_STATUS_UPDATES = False
settings.NOTIFY_UNKNOWN_BYTES = False
settings.SHOW_VARIANT_WARNINGS = False
settings.SHOW_SCENARIO_VERSION_WARNINGS = False
settings.ENABLE_XS_CHECK_INTEGRATION = False


def leer_json(ruta: Path) -> Any:
    try:
        return json.loads(Path(ruta).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError) as e:
        raise entrada.EntradaInvalida(f"no se puede leer {ruta}: {e}") from None
    except json.JSONDecodeError as e:
        raise entrada.EntradaInvalida(f"JSON mal formado en {ruta}: {e}") from None


def generar(raiz: Any, salida: Path) -> Dict[str, Any]:
    """Genera el escenario en {@code salida} (escritura atómica: o queda entero o no queda)."""
    from AoE2ScenarioParser.scenarios.aoe2_de_scenario import AoE2DEScenario

    tipo = entrada.cabecera(raiz)
    fn = TIPOS.get(tipo)
    if fn is None:
        raise entrada.EntradaInvalida(f"tipo de escenario desconocido: {tipo!r} (conocidos: {', '.join(sorted(TIPOS))})")
    scn = AoE2DEScenario.from_default()
    detalle = fn(scn, raiz)
    salida = Path(salida).resolve()
    salida.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".aoe2radar-", suffix=".aoe2scenario", dir=salida.parent)
    os.close(fd)
    try:
        scn.write_to_file(tmp)
        os.replace(tmp, salida)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    return {"tipo": tipo, "version_herramienta": __version__, **detalle}
