# Esquema de entrada, versión 1

Un JSON en UTF-8. Campos comunes a todos los tipos:

| Campo | Tipo | Obligatorio | Qué es |
|---|---|---|---|
| `version` | entero | sí | Versión del esquema. Esta herramienta entiende la `1`. |
| `tipo` | texto | sí | Qué escenario generar. Hoy solo `"batalla"`. |
| `nombre` | texto | no | Título descriptivo (no cambia el archivo). |
| `idioma` | `"es"` \| `"en"` | no (`"es"`) | Idioma de los mensajes que el escenario escribe en el chat. |

Si `version` no es 1, o `tipo` no se conoce, la herramienta sale con código 2 y no escribe nada.

## Tipo `batalla`

Dos ejércitos frente a frente: J1 (azul, humano) a la izquierda, J2 (rojo, ordenador) a la derecha.

```json
{
  "version": 1,
  "tipo": "batalla",
  "nombre": "10 caballeros + 5 ballesteros contra 20 piqueros",
  "idioma": "es",
  "separacion": 8,
  "ring": {"activo": true, "lado": 0},
  "colina": {"bajo": 1, "altura": 2},
  "control": {"p2_ataca": true, "p1_ataca": false, "espera_s": 3},
  "medir": true,
  "mapa": {"tamano": 0},
  "jugadores": [
    {"civ": "Franks", "edad": 4, "tecnologias": [67, 68, 75], "por_fila": 8, "espaciado": 1.0,
     "grupos": [{"unidad": 38, "cantidad": 10, "nombre": "Caballero"},
                {"unidad": 24, "cantidad": 5, "nombre": "Ballestero"}]},
    {"civ": "Teutons", "edad": 4, "tecnologias": [],
     "grupos": [{"unidad": 358, "cantidad": 20, "nombre": "Piquero"}]}
  ]
}
```

| Campo | Tipo | Por defecto | Qué es |
|---|---|---|---|
| `separacion` | número 0-60 | 8 | Casillas entre la primera fila de J1 y la de J2. |
| `ring.activo` | bool | true | Recinto cerrado: fuera de él, agua profunda (nadie sale a pie). |
| `ring.lado` | entero 0-200 | 0 | Lado del recinto en casillas. 0 = el justo para los ejércitos con 6 casillas de aire. Si se pide menos de lo necesario, se usa lo necesario. |
| `colina.bajo` | 0, 1, 2 | 0 | 0 sin colina; 1 colina bajo J1; 2 colina bajo J2. |
| `colina.altura` | 1-7 | 2 | Niveles de elevación de la colina. |
| `control.p2_ataca` | bool | true | A los `espera_s` segundos, J2 «ataca moviéndose» hacia el centro de J1. |
| `control.p1_ataca` | bool | false | Lo mismo para J1 (para medir sin tocar nada). |
| `control.espera_s` | 0-60 | 3 | Segundos antes de la orden de ataque. |
| `medir` | bool | false | Script XS que, al quedarse un lado sin unidades, escribe en el chat el ganador, el tiempo de pelea (desde la orden de ataque) y los supervivientes por tipo. |
| `mapa.tamano` | 0-240 | 0 | Lado del mapa. 0 = automático (mínimo 60). |
| `jugadores` | lista de 2 | — | J1 y J2, en ese orden. |

Cada jugador:

| Campo | Tipo | Por defecto | Qué es |
|---|---|---|---|
| `civ` | texto | — | Clave de civilización de aoe2techtree (`"Franks"`, `"Hindustanis"`…). |
| `edad` | 1-4 | — | Edad inicial: 1 Oscura, 2 Feudal, 3 Castillos, 4 Imperial. |
| `tecnologias` | lista de enteros | `[]` | Ids de tecnología del juego. Se investigan al empezar (efecto «Research Technology» forzado, sin edificio). Quien llama decide cuáles valen para la civ. |
| `grupos` | lista (≥ 1) | — | `{unidad, cantidad, nombre?}`. `unidad`: id de unidad del juego. Van **en orden de delante a atrás**: la herramienta no sabe qué unidad es de cuerpo a cuerpo. `nombre` solo se usa en el chat de la medición. |
| `por_fila` | entero 0-200 | 0 | Unidades por fila. 0 = la mitad del total, hasta 20. |
| `espaciado` | número 0,3-4 | 1,0 | Casillas entre centros de unidades vecinas. |

Como mucho 200 unidades por jugador.

## Salida

- Código 0: escenario escrito (escritura atómica: o el archivo queda entero o no queda).
- Código 2: entrada inválida (el mensaje dice qué campo).
- Código 3: error al generar o al escribir.

Con `--resultado ruta.json` escribe además `{"ok": true, "salida": "...", "tipo": "batalla", "tamano": 60, "unidades": 35, ...}`
o `{"ok": false, "codigo": 2|3, "error": "..."}`. Quien llama sin consola debe leer este archivo.
