"""aoe2radar-escenarios: genera escenarios de AoE2 DE (.aoe2scenario) a partir de un JSON.

Programa independiente bajo GPL-3.0. Usa AoE2ScenarioParser (GPL-3.0, KSneijders) para escribir el formato.
aoe2radar lo invoca como proceso externo y solo se comunica con él por archivos.
"""

__version__ = "1.0.0"

#: Versión del esquema JSON de entrada que entiende esta herramienta.
VERSION_ESQUEMA = 1
