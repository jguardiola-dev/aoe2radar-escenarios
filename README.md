# aoe2radar-escenarios

*English below.*

Programa de línea de órdenes que genera escenarios de **Age of Empires II: Definitive Edition** (`.aoe2scenario`) a
partir de un JSON. Lo usa [aoe2radar](https://github.com/jguardiola-dev/aoe2radar) para «Enviar al juego» una batalla
compuesta en el simulador de combate (Herramientas › Combate › Grupos): en vez de montarla a mano en el editor, sale
un escenario listo para jugar en *Un jugador › Escenario personalizado*.

## Qué hace

```
python -m aoe2radar_escenarios entrada.json salida.aoe2scenario [--resultado resultado.json]
python -m aoe2radar_escenarios --version
escenarios.exe entrada.json salida.aoe2scenario [--resultado resultado.json]     (versión empaquetada)
```

El JSON de entrada sigue un esquema propio, versionado y documentado en [docs/esquema-v1.md](docs/esquema-v1.md).
Hoy hay un tipo de escenario, `"batalla"`:

- Mapa pequeño (60×60 o lo que haga falta) de hierba lisa, sin recursos, sin centro urbano y sin aldeanos.
- **Ring**: recinto cerrado; fuera, agua profunda (nadie se escapa a pie, nada se puede romper).
- J1 (azul) y J2 (rojo) con su civilización y su edad; enemigos; visión total del mapa y de las unidades del otro.
- Las unidades en formación, una frente a otra, con la separación pedida.
- **Colina** opcional: el terreno se eleva bajo J1 o bajo J2.
- **Mejoras**: un trigger investiga al empezar las tecnologías pedidas (efecto «Research Technology» forzado).
- **Quién controla qué**: J1 es humano y J2 ordenador. Todas las unidades en postura agresiva desde el primer instante.
  A los pocos segundos, J2 «ataca moviéndose» hacia J1. Con `control.p1_ataca`, J1 también avanza solo (aoe2radar lo activa al pedir medición, para que la pelea se
  resuelva sin tocar nada y sea comparable con el simulador). J2 no lleva script de IA: si el juego le asigna la IA
  por defecto, puede que además micree. La victoria es «personalizada» sin condiciones: el escenario no se cierra al
  acabar la pelea, para poder leer el chat.
- **Dificultad de la IA**: el formato de escenario no la guarda (se elige al lanzarlo). El objetivo pide «Difícil» y un
  script XS avisa en el chat si la partida no está en Difícil.
- **Textos en el escenario** (siempre): el objetivo (pestaña Mensajes › Instrucciones, se ve en el panel de objetivos),
  un aviso en pantalla al empezar (quién eres y qué va a pasar) y, al quedarse un lado sin unidades militares, «Gana J1»,
  «Gana J2» o «Empate» en pantalla durante 2 minutos.
- **Medición** opcional: un script XS escribe en el chat, al quedarse un lado sin unidades, quién ganó, el tiempo de
  pelea (desde la orden de ataque) y los supervivientes por tipo.

Códigos de salida: 0 bien, 2 entrada inválida, 3 error al generar. La escritura es atómica.

## Cómo la usa aoe2radar

aoe2radar **nunca** carga este código: escribe el JSON en una carpeta temporal, lanza `escenarios.exe`
como proceso externo (sin ventana, con tiempo límite), lee `--resultado` y deja el `.aoe2scenario` en la carpeta de
escenarios del perfil del juego (`%USERPROFILE%\Games\Age of Empires 2 DE\<perfil>\resources\_common\scenario`).

El instalador de aoe2radar lleva este programa ya compilado en `herramientas\escenarios\` junto con esta licencia y un
`FUENTES.txt` con el enlace a este repositorio. Son dos programas separados distribuidos juntos (agregación, GPL-3.0
sección 5): cada uno conserva su licencia y solo se comunican por archivos.

## Licencia y créditos

GNU GPL v3 (ver [LICENSE](LICENSE)). Este programa usa
[**AoE2ScenarioParser**](https://github.com/KSneijders/AoE2ScenarioParser) 0.9.1, de **KSneijders** y colaboradores,
también GPL-3.0: es la librería que sabe leer y escribir el formato de escenario de AoE2 DE. Gracias.

Nota: el campo «License» de los metadatos de PyPI de AoE2ScenarioParser 0.9.1 dice MIT, pero el archivo LICENSE que
trae el paquete es la GPL v3. Este proyecto sigue al archivo LICENSE.

El `.exe` incluye además el intérprete de Python (licencia PSF) y el cargador de PyInstaller (GPL v2 con excepción para
el cargador); ver [empaquetado/FUENTES.txt](empaquetado/FUENTES.txt). No incluye `xs-check` (el linter de XS que trae la
librería): solo lo usan los tests.

Age of Empires II © Microsoft Corporation. Este programa no está respaldado ni afiliado a Microsoft.

## Desarrollo

```powershell
python -m venv venv
venv\Scripts\pip install -r requirements-dev.txt -e .
venv\Scripts\python -m pytest            # genera escenarios, los relee con la librería y comprueba unidades, civs, colina, triggers y el XS
.\empaquetado\construir-exe.ps1          # dist\escenarios\escenarios.exe (+ LICENSE y FUENTES.txt) y una prueba de humo
```

`muestras\` guarda escenarios de ejemplo generados para abrirlos en el juego.

### Estructura y cómo añadir un tipo de escenario

```
aoe2radar_escenarios/
  __main__.py      CLI (argumentos, códigos de salida, --resultado)
  generador.py     carga el escenario base de la librería, despacha al tipo y escribe (atómico)
  entrada.py       validación del JSON (solo forma; nada de conocimiento del juego)
  piezas/          piezas reutilizables por cualquier tipo
    mapa.py          tamaño, terreno, ring de agua, colinas
    jugadores.py     civ, edad, recursos, población, humano/ordenador, diplomacia, cámara, visión
    colocacion.py    formaciones y plano del mapa (geometría pura)
    mejoras.py       tecnologías investigadas al empezar
    control.py       órdenes al empezar (postura, atacar moviéndose)
    medicion.py      XS que mide y escribe en el chat
  tipos/
    __init__.py      registro TIPOS = {"batalla": batalla.generar}
    batalla.py       compone las piezas para una batalla
```

Para añadir un tipo (p. ej. `"build_order"`, `"micro"`, `"momento"`, `"calibracion"`, `"cajon"`):

1. Documenta su forma en `docs/esquema-v1.md` (los tipos nuevos no cambian la versión del esquema; un cambio
   incompatible en un tipo existente sí: `version: 2`).
2. Escribe su validación en `entrada.py` (una función que devuelve un dataclass).
3. Crea `tipos/<tipo>.py` con `generar(scn, raiz) -> dict` que use las piezas (y añade piezas nuevas en `piezas/`
   si hacen falta: edificios, objetivos, avisos de tiempo…).
4. Regístralo en `tipos/__init__.py` y añade tests en `tests/` que generen, relean y comprueben.

---

# aoe2radar-escenarios (English)

A command-line program that generates **Age of Empires II: Definitive Edition** scenarios (`.aoe2scenario`) from a
JSON file. [aoe2radar](https://github.com/jguardiola-dev/aoe2radar) uses it for "Send to game" on a battle built in its
combat simulator (Tools › Combat › Groups), so the battle comes out as a ready-to-play scenario
(*Single Player › Custom Scenario*) instead of being rebuilt by hand in the editor.

Usage, input schema and behaviour are described above (in Spanish) and in [docs/esquema-v1.md](docs/esquema-v1.md).
In short, the `"batalla"` (battle) type creates a small flat map with a closed water ring, P1 (human) and P2
(computer) with their civilizations and ages, both armies in formation facing each other, an optional hill under one
side, the requested technologies researched by a trigger at start, full visibility, P2 attack-moving towards P1 after
a few seconds, and optionally an XS script that writes the winner, fight time and survivors to the chat.

**How aoe2radar uses it:** aoe2radar never loads this code. It writes the JSON to a temporary folder, runs
`escenarios.exe` as an external process (no window, with a timeout), reads the `--resultado` file and puts the
scenario in the game profile's scenario folder. The aoe2radar installer ships this program prebuilt in
`herramientas\escenarios\` with this license and a `FUENTES.txt` pointing to this repository: two separate programs
distributed together (an aggregate, GPL-3.0 section 5), each under its own license, communicating only through files.

**License and credits:** GNU GPL v3. Built on [**AoE2ScenarioParser**](https://github.com/KSneijders/AoE2ScenarioParser)
0.9.1 by **KSneijders** and contributors (GPL-3.0), the library that reads and writes the AoE2 DE scenario format.
Thank you. The `.exe` also contains the Python runtime (PSF license) and the PyInstaller bootloader (GPL v2 with the
bootloader exception). Age of Empires II © Microsoft Corporation; not endorsed by or affiliated with Microsoft.

**Adding a scenario type:** validation in `entrada.py`, a `tipos/<type>.py` module with `generar(scn, raiz) -> dict`
built from the reusable `piezas/` (map and ring, players, placement, technologies, orders, measurement), one line in
`tipos/__init__.py`, and tests that generate, re-read and check the scenario.
