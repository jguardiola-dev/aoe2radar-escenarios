"""Tipo «batalla»: dos ejércitos frente a frente en un recinto, con mejoras, colina opcional y medición opcional.

Decisiones (ver README):
- J1 humano, J2 ordenador. Todas las unidades en postura agresiva desde el primer instante. J2 avanza atacando hacia
  J1 al cabo de ``control.espera_s`` segundos; J1 solo si ``control.p1_ataca`` (aoe2radar lo activa al pedir medición,
  para que la pelea se resuelva sin tocar nada).
- La dificultad de la IA no se puede fijar en el archivo (el formato no la guarda): el objetivo pide «Difícil» y un XS
  avisa en el chat si no lo es. El objetivo, el aviso de inicio y «Gana J1/J2» van siempre (``piezas.avisos``).
- Sin TC, sin aldeanos, sin recursos. Victoria «personalizada» sin condiciones: el escenario NO termina cuando un lado
  se queda sin unidades (así se puede leer el chat de la medición).
"""
from __future__ import annotations

from AoE2ScenarioParser.datasets.trigger_lists.victory_condition import VictoryCondition

from .. import entrada
from ..piezas import avisos, colocacion, control, jugadores, mapa, medicion, mejoras


def generar(scn, raiz: dict) -> dict:
    b = entrada.batalla(raiz)

    # Mapa y colocación
    formaciones = [colocacion.formacion([(g.unidad, g.cantidad) for g in j.grupos], j.por_fila, j.espaciado) for j in b.jugadores]
    plano = colocacion.planificar(formaciones, b.separacion, b.ring.activo, b.ring.lado, b.tamano_mapa)
    mapa.preparar(scn, plano.tamano, plano.recinto)
    if b.colina.bajo in (1, 2):
        mapa.colina(scn, plano.zonas[b.colina.bajo - 1], b.colina.altura, plano.recinto)

    # Jugadores
    jugadores.configurar(scn, [(j.civ, j.edad) for j in b.jugadores], [True, False])
    for i, (cx, cy) in enumerate(plano.centros, start=1):
        jugadores.camara(scn, i, cx, cy)

    # Unidades: J1 mira hacia +x, J2 hacia -x (rotación en radianes, opuestas)
    um = scn.unit_manager
    um.units = [[] for _ in range(9)]
    for p, unidad, x, y in plano.unidades:
        um.add_unit(player=p, unit_const=unidad, x=x, y=y, z=float(mapa.elevacion(scn, x, y)),
                    rotation=ROTACION[p])

    # Triggers
    scn.trigger_manager.triggers = []
    jugadores.vision_total(scn, 2)
    for i, j in enumerate(b.jugadores, start=1):
        mejoras.investigar(scn, i, j.tecnologias)
    ordenes = []
    if b.control.p1_ataca:
        ordenes.append((1, *plano.centros[1]))
    if b.control.p2_ataca:
        ordenes.append((2, *plano.centros[0]))
    control.al_ataque(scn, plano.tamano, b.control.espera_s, ordenes)
    avisos.anadir(scn, b.idioma, b.control.espera_s, b.control.p1_ataca, b.control.p2_ataca, b.medir)
    if b.medir:
        grupos = [[(g.unidad, g.nombre) for g in j.grupos] for j in b.jugadores]
        medicion.anadir(scn, medicion.script(grupos, b.control.espera_s, b.idioma))

    # Opciones del escenario
    om = scn.option_manager
    om.victory_condition = VictoryCondition.CUSTOM
    om.victory_custom_conditions_required = False

    return {"tamano": plano.tamano, "unidades": len(plano.unidades), "recinto": plano.recinto}


#: Rotación inicial por jugador (radianes). Opuestas: se miran. Por confirmar en el juego cuál es «hacia +x».
ROTACION = {1: 0.7853981633974483, 2: 3.9269908169872414}
