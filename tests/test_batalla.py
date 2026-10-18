"""Genera escenarios de batalla, los relee con la propia librería y comprueba lo que importa."""
from __future__ import annotations

import copy
import json
import subprocess
from pathlib import Path

import pytest
from AoE2ScenarioParser.datasets.object_support import Civilization, StartingAge
from AoE2ScenarioParser.datasets.effects import EffectId
from AoE2ScenarioParser.datasets.terrains import TerrainId
from AoE2ScenarioParser.datasets.trigger_lists.victory_condition import VictoryCondition
from AoE2ScenarioParser.scenarios.aoe2_de_scenario import AoE2DEScenario

from aoe2radar_escenarios import __main__ as cli
from aoe2radar_escenarios import generador
from aoe2radar_escenarios.piezas import colocacion, medicion

AQUI = Path(__file__).parent
EJEMPLO = json.loads((AQUI / "batalla_ejemplo.json").read_text(encoding="utf-8"))
import AoE2ScenarioParser as _asp  # noqa: E402

XS_CHECK = Path(_asp.__file__).parent / "dependencies" / "xs-check" / "xs-check.exe"


def _generar(tmp_path, raiz) -> AoE2DEScenario:
    salida = tmp_path / "prueba.aoe2scenario"
    generador.generar(raiz, salida)
    assert salida.is_file() and salida.stat().st_size > 0
    return AoE2DEScenario.from_file(str(salida))


def test_unidades_civs_y_edad(tmp_path):
    scn = _generar(tmp_path, EJEMPLO)
    um = scn.unit_manager
    j1 = um.get_player_units(1)
    j2 = um.get_player_units(2)
    assert sorted(u.unit_const for u in j1) == sorted([38] * 10 + [24] * 5)
    assert [u.unit_const for u in j2] == [358] * 20
    assert um.get_player_units(0) == [], "sin nada de Gaia: ni recursos, ni árboles, ni TC"
    pm = scn.player_manager
    assert pm.active_players == 2
    assert pm.players[1].civilization == Civilization.FRANKS
    assert pm.players[2].civilization == Civilization.TEUTONS
    assert pm.players[1].starting_age == StartingAge.IMPERIAL_AGE
    assert pm.players[1].human and not pm.players[2].human
    assert (pm.players[1].food, pm.players[1].wood, pm.players[1].gold, pm.players[1].stone) == (0, 0, 0, 0)
    # se miran: todo J1 a la izquierda de todo J2, con la separación pedida entre frentes
    assert max(u.x for u in j1) + EJEMPLO["separacion"] <= min(u.x for u in j2)


def test_colina_bajo_j1_y_ring_de_agua(tmp_path):
    scn = _generar(tmp_path, EJEMPLO)
    mm = scn.map_manager
    um = scn.unit_manager
    for u in um.get_player_units(1):
        assert mm.get_tile(int(u.x), int(u.y)).elevation == 2, "J1 en lo alto"
        assert u.z == 2
    for u in um.get_player_units(2):
        assert mm.get_tile(int(u.x), int(u.y)).elevation == 0, "J2 en el llano"
    for u in um.get_all_units():
        assert mm.get_tile(int(u.x), int(u.y)).terrain_id == TerrainId.GRASS_1, "ninguna unidad en el agua"
    assert mm.get_tile(0, 0).terrain_id == TerrainId.WATER_DEEP
    assert mm.get_tile(mm.map_size // 2, mm.map_size // 2).terrain_id == TerrainId.GRASS_1
    assert mm.map_size == 60


def test_sin_ring_ni_colina(tmp_path):
    raiz = copy.deepcopy(EJEMPLO)
    raiz["ring"] = {"activo": False}
    raiz["colina"] = {"bajo": 0}
    scn = _generar(tmp_path, raiz)
    assert all(t.terrain_id == TerrainId.GRASS_1 and t.elevation == 0 for t in scn.map_manager.terrain)


def test_colina_bajo_j2(tmp_path):
    raiz = copy.deepcopy(EJEMPLO)
    raiz["colina"] = {"bajo": 2, "altura": 3}
    scn = _generar(tmp_path, raiz)
    mm = scn.map_manager
    assert all(mm.get_tile(int(u.x), int(u.y)).elevation == 3 for u in scn.unit_manager.get_player_units(2))
    assert all(mm.get_tile(int(u.x), int(u.y)).elevation == 0 for u in scn.unit_manager.get_player_units(1))


def test_triggers_mejoras_vision_ataque_y_victoria(tmp_path):
    scn = _generar(tmp_path, EJEMPLO)
    ts = {t.name: t for t in scn.trigger_manager.triggers}
    assert "aoe2radar: vision total" in ts
    mej = ts["aoe2radar: mejoras J1"]
    techs = [e.technology for e in mej.effects if e.effect_type == EffectId.RESEARCH_TECHNOLOGY]
    assert techs == EJEMPLO["jugadores"][0]["tecnologias"]
    assert all(e.source_player == 1 and e.force_research_technology == 1 for e in mej.effects)
    assert "aoe2radar: mejoras J2" not in ts, "J2 sin mejoras: sin trigger"
    ataque = ts["aoe2radar: al ataque"]
    movs = [e for e in ataque.effects if e.effect_type == EffectId.ATTACK_MOVE]
    assert sorted(e.source_player for e in movs) == [1, 2]
    assert ataque.conditions[0].timer == 3
    assert scn.option_manager.victory_condition == VictoryCondition.CUSTOM


def test_medicion_xs_presente_y_valido(tmp_path):
    scn = _generar(tmp_path, EJEMPLO)
    xs = scn.xs_manager._get_scenario_xs()
    assert medicion.NOMBRE_REGLA in xs and "xsChatData" in xs
    sin = copy.deepcopy(EJEMPLO)
    sin["medir"] = False
    assert medicion.NOMBRE_REGLA not in _generar(tmp_path, sin).xs_manager._get_scenario_xs()


@pytest.mark.skipif(not XS_CHECK.is_file(), reason="xs-check no está (solo Windows)")
@pytest.mark.parametrize("idioma", ["es", "en"])
def test_xs_pasa_xs_check(tmp_path, idioma):
    xs = medicion.script([[(38, 'Caballero "raro" 100%'), (24, "Ballestero")], [(358, "Piquero")]], 3, idioma)
    f = tmp_path / "medir.xs"
    f.write_text(xs, encoding="utf-8")
    r = subprocess.run([str(XS_CHECK), "-w", str(f)], capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert r.returncode == 0, r.stdout + r.stderr


def test_formacion_geometria():
    p = colocacion.formacion([(38, 10), (24, 5)], 8, 1.0)
    assert len(p) == 15
    assert [x.unidad for x in p[:10]] == [38] * 10, "el primer grupo, delante"
    assert {x.fondo for x in p} == {0.0, 1.0}
    assert colocacion.por_fila(15, 0) == 8 and colocacion.por_fila(60, 0) == 20
    assert colocacion.huella(p) == (2.0, 8.0)


def test_mapa_crece_si_no_cabe(tmp_path):
    raiz = copy.deepcopy(EJEMPLO)
    raiz["separacion"] = 40
    raiz["jugadores"][1]["por_fila"] = 1          # 20 en columna: 20 casillas de fondo
    scn = _generar(tmp_path, raiz)
    assert scn.map_manager.map_size > 60
    mm = scn.map_manager
    assert all(mm.get_tile(int(u.x), int(u.y)).terrain_id == TerrainId.GRASS_1 for u in scn.unit_manager.get_all_units())


# ------------------------------------------------------------------------------------------------ CLI

def test_cli_bien_y_resultado(tmp_path):
    entrada = tmp_path / "e.json"
    entrada.write_text(json.dumps(EJEMPLO), encoding="utf-8")
    salida, res = tmp_path / "s.aoe2scenario", tmp_path / "r.json"
    assert cli.main([str(entrada), str(salida), "--resultado", str(res)]) == 0
    r = json.loads(res.read_text(encoding="utf-8"))
    assert r["ok"] and r["tipo"] == "batalla" and r["unidades"] == 35
    assert not list(tmp_path.glob(".aoe2radar-*")), "sin temporales"


@pytest.mark.parametrize("cambio, texto", [
    ({"version": 2}, "versión"),
    ({"tipo": "cine"}, "tipo de escenario desconocido"),
    ({"separacion": -1}, "separacion"),
])
def test_cli_entrada_invalida(tmp_path, cambio, texto):
    entrada = tmp_path / "e.json"
    entrada.write_text(json.dumps({**EJEMPLO, **cambio}), encoding="utf-8")
    salida, res = tmp_path / "s.aoe2scenario", tmp_path / "r.json"
    assert cli.main([str(entrada), str(salida), "--resultado", str(res)]) == 2
    r = json.loads(res.read_text(encoding="utf-8"))
    assert not r["ok"] and texto in r["error"]
    assert not salida.exists()


def test_civ_desconocida(tmp_path):
    raiz = copy.deepcopy(EJEMPLO)
    raiz["jugadores"][0]["civ"] = "Atlantes"
    entrada = tmp_path / "e.json"
    entrada.write_text(json.dumps(raiz), encoding="utf-8")
    assert cli.main([str(entrada), str(tmp_path / "s.aoe2scenario")]) == 2


def test_json_roto(tmp_path):
    entrada = tmp_path / "e.json"
    entrada.write_text("{roto", encoding="utf-8")
    assert cli.main([str(entrada), str(tmp_path / "s.aoe2scenario")]) == 2


#: Las claves de civ de aoe2techtree (data.json de aoe2radar, octubre de 2026): todas deben existir en la librería.
CIVS_TECHTREE = ['Armenians', 'Aztecs', 'Bengalis', 'Berbers', 'Bohemians', 'Britons', 'Bulgarians', 'Burgundians', 'Burmese',
                 'Byzantines', 'Celts', 'Chinese', 'Cumans', 'Danes', 'Dravidians', 'Ethiopians', 'Franks', 'Georgians', 'Goths',
                 'Gurjaras', 'Hindustanis', 'Huns', 'Incas', 'Italians', 'Japanese', 'Jurchens', 'Khitans', 'Khmer', 'Koreans',
                 'Lithuanians', 'Magyars', 'Malay', 'Malians', 'Mapuche', 'Mayans', 'Mongols', 'Muisca', 'Persians', 'Poles',
                 'Portuguese', 'Romans', 'Saracens', 'Saxons', 'Shu', 'Sicilians', 'Slavs', 'Spanish', 'Tatars', 'Teutons', 'Tupi',
                 'Turks', 'Varangians', 'Vietnamese', 'Vikings', 'Wei', 'Wu']


def test_todas_las_civs_del_tech_tree():
    from aoe2radar_escenarios.piezas.jugadores import civilizacion
    for c in CIVS_TECHTREE:
        assert civilizacion(c).name == c.upper()
