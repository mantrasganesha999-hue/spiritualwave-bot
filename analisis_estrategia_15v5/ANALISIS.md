# Análisis de la estrategia 15m vs 5m — bot V1.09 (filtros de Delta)

> **Alcance.** Este documento analiza **la estrategia tal como está implementada**.
> No introduce, propone ni implementa ninguna estrategia de trading distinta.
> Todas las mejoras señaladas son correcciones de errores, retrasos, sincronización
> o ejecución **dentro de la estrategia existente**, manteniendo su comportamiento
> y objetivo original.
>
> **Nota sobre el repositorio.** El repositorio `spiritualwave-bot` no contiene el
> bot de trading (es un pipeline de vídeo/YouTube). El código analizado es el que
> fue aportado en el enunciado. Los simuladores de esta carpeta reproducen su
> lógica de decisión **línea por línea** para poder ejecutarla sin red.

---

## 1. Qué hace realmente la estrategia

No es una estrategia direccional. Es un **par cubierto entre dos mercados que
liquidan en el mismo instante pero contra referencias distintas**.

### 1.1 Alineación temporal

```
id_15m_actual = ahora - (ahora % 900)          # vela de 15m en curso
id_5m_v3      = id_15m_actual + 600            # TERCERA vela de 5m
```

La tercera vela de 5m (minutos 10→15) **cierra en el mismo segundo** que la vela
de 15m. Esta alineación es correcta: ambos mercados liquidan contra el mismo
precio de cierre `C`. Lo que difiere es el **open** de referencia:

| Mercado | Open de referencia | Momento |
|---|---|---|
| 15m | `open_15m` | T-900 s |
| 5m (3ª) | `open_5m` | T-300 s |

### 1.2 Señal y dirección

```python
delta_15m = spot - open_15m
delta_5m  = spot - open_5m

if delta_15m >= 0:  token_15m, token_5m = t_15m_yes, t_5m_no    # "UP (YES)"
else:               token_15m, token_5m = t_15m_no,  t_5m_yes   # "DOWN (NO)"
```

**La dirección se decide únicamente con el signo de `delta_15m`.** El signo de
`delta_5m` no interviene en ningún punto de la decisión — sólo su valor absoluto,
y sólo como filtro de admisión. Éste es el origen del problema central (§3).

Se compra siempre el **lado opuesto** en el mercado de 5m. No es una apuesta
doble: es una cobertura.

### 1.3 Condición de compra (`es_oportunidad`)

```python
cumple_deltas = abs(delta_15m) >= 20.0 and abs(delta_5m) >= 15.0

es_oportunidad = (
    cumple_deltas
    and 0.15 < ask_15m < 0.90 and 0.02 < ask_5m < 0.95
    and combo_cost <= 0.97
    and notional_15m >= 1.0 and notional_5m >= 1.0
    and profundidad_suficiente
)
```

Ventana activa: los **últimos 180 s** de la vela de 15m. Tamaño fijo: **10 combos**.

---

## 2. Matriz de liquidación: de dónde sale el dinero

Sea `C` el precio de cierre, `o15 = open_15m`, `o5 = open_5m`.
Caso **UP** (se compró 15m-UP + 5m-DOWN):

| Condición | 15m-UP | 5m-DOWN | Payout |
|---|---|---|---|
| `C > o15` y `C > o5` | $1 | $0 | **$1** |
| `C > o15` y `C ≤ o5` | $1 | $1 | **$2** |
| `C ≤ o15` y `C ≤ o5` | $0 | $1 | **$1** |
| `C ≤ o15` y `C > o5` | $0 | $0 | **$0** |

El payout es **$1 casi siempre**, con una única banda de precio donde vale $2 y
una única banda donde vale $0. **Las dos bandas nunca coexisten.** Cuál de las dos
existe depende exclusivamente de la posición relativa de los dos opens:

```
o5 - o15 = delta_15m - delta_5m
```

---

## 3. El hallazgo estructural: cuándo el par es seguro y cuándo no

> **Regla unificada (demostrada en `motor_estrategia.clasificar_configuracion`):**
>
> Existe banda de **pérdida total ($0)** si y sólo si
> `sign(delta_5m) == sign(delta_15m)` **y** `|delta_5m| > |delta_15m|`.
>
> El ancho de esa banda es exactamente `|delta_5m| - |delta_15m|` dólares.

Tres regímenes:

| Configuración | Condición | Payout mínimo | Banda |
|---|---|---|---|
| **SEGURO-MAX** | signos **opuestos** | $1 | $2 de ancho `\|d15\|+\|d5\|` |
| **SEGURO** | mismo signo, `\|d15\| > \|d5\|` | $1 | $2 de ancho `\|d15\|-\|d5\|` |
| **NEUTRO** | `\|d15\| = \|d5\|` | $1 | ninguna — siempre $1 |
| **RIESGO** | mismo signo, `\|d5\| > \|d15\|` | **$0** | $0 de ancho `\|d5\|-\|d15\|` |

**El filtro actual no distingue entre estos cuatro casos.** Mapa del espacio que
el filtro de delta aprueba (`python3 sim_barrido.py`):

```
  d15\d5   -60  -50  -40  -30  -20  -10    0   10   20   30   40   50   60
    -60     =    S    S    S    S    .    .    .    S    S    S    S    S
    -50     X    =    S    S    S    .    .    .    S    S    S    S    S
    -40     X    X    =    S    S    .    .    .    S    S    S    S    S
    -30     X    X    X    =    S    .    .    .    S    S    S    S    S
    -20     X    X    X    X    =    .    .    .    S    S    S    S    S
    -10     .    .    .    .    .    .    .    .    .    .    .    .    .
      0     .    .    .    .    .    .    .    .    .    .    .    .    .
     10     .    .    .    .    .    .    .    .    .    .    .    .    .
     20     S    S    S    S    S    .    .    .    =    X    X    X    X
     30     S    S    S    S    S    .    .    .    S    =    X    X    X
     40     S    S    S    S    S    .    .    .    S    S    =    X    X
     50     S    S    S    S    S    .    .    .    S    S    S    =    X
     60     S    S    S    S    S    .    .    .    S    S    S    S    =

  '.' rechazado por filtro delta   'S' SEGURO   'X' RIESGO ($0 posible)   '=' NEUTRO

  Sobre la rejilla [-150,+150] paso 1 USD:
    combinaciones que el filtro de delta aprueba .... 71.264
    de esas, estructuralmente de RIESGO ............. 17.030  (23.9%)
```

Casi una de cada cuatro señales admitidas por el filtro tiene una banda de
pérdida total, y **el código no lo mide en ningún momento**.

Los umbrales elegidos (20 para 15m, 15 para 5m) aciertan sólo en el caso límite:
cuando ambos deltas están justo en su mínimo (`d15=+20`, `d5=+15`), se cumple
`|d15| > |d5|` y la configuración es segura. Pero el filtro no impone ninguna
relación **entre** los dos deltas — sólo un mínimo a cada uno por separado.

---

## 4. El hallazgo central: selección adversa

Si el par es seguro, el payout mínimo es $1, luego su **valor teórico es ≥ $1.00**.
Un mercado eficiente nunca lo ofrecerá a $0.97. El filtro `combo_cost <= 0.97`
es, en la práctica, un **detector de la banda de pérdida**: los combos baratos
son baratos porque el mercado sabe que pueden valer $0.

Barrido con precios de mercado eficiente (`python3 sim_barrido.py`), BTC $100k,
volatilidad 50 % anual, σ(180 s) = $119,5:

```
BARRIDO con mercado EFICIENTE  |  T-180s  |  3721 combinaciones (d15,d5)
  Rechazados por filtro de DELTA .......   697  (18.7%)
  Rechazados por rango de precio .......   224  ( 6.0%)
  Rechazados por combo > 0.97 ..........  2254  (60.6%)
  ACEPTADOS (dispara compra) ...........   546  (14.7%)
  De los aceptados:
     config RIESGO  (existe payout $0) .   546  (100.0%)
     config SEGURA  (payout mínimo $1) .     0  (  0.0%)
     con EV NEGATIVO ...................   546  (100.0%)
  EV medio por operación ............... $-0.204
  EV medio con slippage +0.01/pata ..... $-0.404
```

El mismo resultado se repite a T-90 s, T-30 s y T-5 s. **Cuando el mercado cotiza
a valor justo, el 100 % de las operaciones que el filtro acepta son de
configuración de riesgo y de esperanza negativa.**

Esto no significa que la estrategia no pueda ganar: significa que **todo su
beneficio depende de capturar dislocaciones reales de precio** (libros
desactualizados, market makers retirados, spreads anchos), no del filtro de delta.
Y capturar dislocaciones es precisamente lo que los retrasos de §6 impiden.

### 4.1 La asimetría riesgo/beneficio

Con `SHARES_A_COMPRAR = 10` y `UMBRAL_MAX_COMBO = 0.97`:

| | Valor |
|---|---|
| Beneficio en el caso normal ($1) | `(1.00 − 0.97) × 10 = ` **$0.30** |
| Pérdida en la banda de $0 | **−$9.70** |
| Aciertos necesarios para no perder | **97.0 %** |
| Con slippage (+$0.01 por pata) el coste real puede llegar a **$0.99** | beneficio **$0.10**, se necesita **99.0 %** |

> **Nota importante sobre el coste real.** `UMBRAL_MAX_COMBO` se aplica al **ask
> observado**, pero la orden se envía a `ask + 0.01` en **cada pata**
> (`_ejecutar_orden_sync`). Una FOK marketable casa contra el ask que está en el
> libro, así que el coste **típico** es el ask; pero si el libro se movió dentro
> del buffer, el coste real llega a **$0.99**, no a $0.97. Además `p_15m` y `p_5m`
> que se devuelven y se registran son **el precio límite, no el fill real**: todos
> los logs, la notificación de Telegram y el `precio_compra` del protocolo de
> emergencia están inflados hasta 2 centavos.

---

## 5. Escenarios detallados

Generados por `python3 sim_escenarios.py`. BTC $100.000, volatilidad 50 % anual,
T-180 s (σ = $119,5), 10 combos por operación.

| Escenario | Δ15m | Δ5m | Señal | Clase | Combo | ¿Compra? | P($0) | EV/op |
|---|---|---|---|---|---|---|---|---|
| E01 Ambos UP, 15m domina | +45,0 | +20,0 | UP (YES) | SEGURO | 0,95 | **SÍ** | 0,00 % | +1,30 |
| E02 Ambos UP, 5m domina | +22,0 | +55,0 | UP (YES) | **RIESGO** | 0,95 | **SÍ** | 10,43 % | **−0,54** |
| E03 Ambos UP en el mínimo del filtro | +20,0 | +15,0 | UP (YES) | SEGURO | 0,94 | **SÍ** | 0,00 % | +0,77 |
| E04 Ambos UP casi idénticos (5m>15m) | +20,0 | +21,0 | UP (YES) | **RIESGO** | 0,95 | **SÍ** | 0,33 % | +0,47 |
| E05 Señales OPUESTAS 15m↑ 5m↓ | +30,0 | −25,0 | UP (YES) | SEGURO-MAX | 0,90 | **SÍ** | 0,00 % | +2,82 |
| E06 Señales OPUESTAS 15m↓ 5m↑ | −30,0 | +25,0 | DOWN (NO) | SEGURO-MAX | 0,90 | **SÍ** | 0,00 % | +2,82 |
| E07 Ambos DOWN, 15m domina | −50,0 | −20,0 | DOWN (NO) | SEGURO | 0,93 | **SÍ** | 0,00 % | +1,66 |
| E08 Ambos DOWN, 5m domina | −21,0 | −60,0 | DOWN (NO) | **RIESGO** | 0,94 | **SÍ** | 12,25 % | **−0,62** |
| E09 Δ15m insuficiente | +12,0 | +40,0 | UP (YES) | RIESGO | 0,90 | no | 9,11 % | +0,09 |
| E10 Δ5m insuficiente | +60,0 | +8,0 | UP (YES) | SEGURO | 0,95 | no | 0,00 % | +2,16 |
| E11 Ambos deltas insuficientes | +5,0 | +3,0 | UP (YES) | SEGURO | 0,97 | no | 0,00 % | +0,37 |
| E12 Deltas OK pero combo caro | +40,0 | +18,0 | UP (YES) | SEGURO | 1,01 | no | 0,00 % | +0,61 |
| E13 ask 15m ≥ 0,90 | +80,0 | +30,0 | UP (YES) | SEGURO | 0,97 | no | 0,00 % | +1,79 |
| E14 ask 15m ≤ 0,15 | +25,0 | +40,0 | UP (YES) | RIESGO | 0,74 | no | 4,82 % | +2,12 |
| E15 Δ15m = 0 (→ UP por `>= 0`) | 0,0 | +30,0 | UP (YES) | RIESGO | 0,90 | no | 9,91 % | +0,01 |
| E16 Δ15m = −0,01 (→ DOWN) | −0,01 | −30,0 | DOWN (NO) | RIESGO | 0,90 | no | 9,91 % | +0,01 |
| E17 Reversión violenta consumada | +21,0 | −80,0 | UP (YES) | SEGURO-MAX | 0,76 | **SÍ** | 0,00 % | +5,58 |
| E18 Tendencia limpia sostenida | +120,0 | +90,0 | UP (YES) | SEGURO | 0,96 | **SÍ** | 0,00 % | +1,08 |
| E19 Aceleración tardía (5m≫15m) | +25,0 | +110,0 | UP (YES) | **RIESGO** | 0,90 | **SÍ** | **23,85 %** | **−1,39** |
| E20 Combo exactamente en el umbral | +40,0 | +25,0 | UP (YES) | SEGURO | 0,97 | **SÍ** | 0,00 % | +0,78 |

### 5.1 Los escenarios que importan

**E19 — Aceleración tardía. El peor caso del filtro actual.**

- Δ15m = **+$25,00** (supera el umbral de 20) · Δ5m = **+$110,00** (supera el de 15)
- Señal: `UP (YES)` → compra `15M_YES` + `5M_NO`
- Condición que **activa**: los dos deltas superan sus umbrales, ask 15m 0,60 y
  ask 5m 0,30 están en rango, combo 0,90 ≤ 0,97, profundidad OK.
- `open_15m = 99.975`, `open_5m = 99.890` → **`open_5m` está $85 por debajo** →
  banda de pérdida total de **$85 de ancho** entre 99.890 y 99.975.
- Precio esperado de entrada: 15m $0,60 · 5m $0,30 → combo $0,90
- Precio límite realmente enviado: 15m **$0,61** · 5m **$0,31** → combo peor caso $0,92
- Coste total: **$9,00** esperado · **$9,20** peor caso
- Distribución: P($2) = 0 % · P($1) = 76,15 % · **P($0) = 23,85 %**
- **Resultado esperado: −$1,39 por operación.** Casi una de cada cuatro veces se
  pierden los $9,00 completos para ganar $1,00 el resto de las veces.

Interpretación en lenguaje de mercado: el precio subió $110 **en los últimos 5
minutos** pero sólo $25 **en los 15 minutos completos**, es decir, venía de caer.
El bot compra "sube en 15m" cuando el movimiento apenas acaba de recuperar
terreno perdido. Un retroceso de $25 lo deja fuera del dinero en las dos patas.

**E05/E06/E17 — Señales no alineadas. El mejor caso, y el filtro lo trata igual.**

Cuando Δ15m y Δ5m tienen **signos opuestos**, no existe banda de pérdida y la
banda de doble premio es la suma de ambos: en E17 (Δ15m=+21, Δ5m=−80) mide **$101
de ancho**, con EV de **+$5,58 por operación**. Son las mejores operaciones que
la estrategia puede hacer y el código las trata exactamente igual que a E19.

**E15/E16 — La discontinuidad en cero.** `delta_15m >= 0` manda a UP y
`delta_15m < 0` manda a DOWN. Una diferencia de un centavo en el spot invierte
por completo el par comprado. Hoy queda tapado porque el filtro exige |Δ15m| ≥ 20,
pero la discontinuidad existe y reaparecería si se bajara el umbral.

**E10 vs E19 — El filtro rechaza lo bueno y acepta lo malo.** E10 (Δ15m=+60,
Δ5m=+8) es **estructuralmente seguro** con EV +$2,16 y se **rechaza** porque
Δ5m < 15. E19 es de riesgo con EV −$1,39 y se **acepta**. El filtro de Δ5m está
invertido respecto a lo que la matriz de liquidación necesita: un Δ5m **pequeño**
frente a Δ15m es lo que hace segura la operación.

---

## 6. Paralelización, bloqueos y retrasos

### 6.1 Lo que sí está bien paralelizado

- Las 5 peticiones HTTP por tick van en un `asyncio.gather` anidado → concurrentes.
- Las dos patas se disparan en `ThreadPoolExecutor` **separados** (`EXECUTOR_LEG_A`
  / `EXECUTOR_LEG_B`), así que el `time.sleep(0.1)` de reintento **no** bloquea el
  event loop y las dos órdenes salen realmente en paralelo.
- El WSS corre en su propia task.

### 6.2 Modelo temporal medido

`python3 sim_latencia.py`:

| Perfil de red | Cadencia **real** del bucle | Retraso detección (peor) | Decisión → matching (peor) |
|---|---|---|---|
| VPS óptimo (mismo DC) | **145 ms** | 170 ms | 215 ms |
| VPS bueno (EU/US) | **220 ms** | 290 ms | 390 ms |
| Cloud genérico | **380 ms** | 540 ms | 770 ms |
| Conexión pobre | **700 ms** | 1.050 ms | 1.510 ms |

**El `await asyncio.sleep(0.1)` sugiere una cadencia de 100 ms que nunca se
alcanza**, porque cada tick espera a la más lenta de 5 peticiones HTTP antes de
volver a dormir. La cadencia real la marca **Gamma**, que es la API más lenta.

Impacto económico del retraso (BTC $100k, token 15m at-the-money):

| Retraso | Movimiento BTC (1σ) | Movimiento precio token | Coste sobre 10 combos |
|---|---|---|---|
| 100 ms | $2,8 | 0,0094 | $0,09 |
| 500 ms | $6,3 | 0,0210 | $0,21 |
| 2.000 ms | $12,6 | 0,0420 | $0,42 |
| 10.000 ms | $28,2 | 0,0940 | $0,94 |

> Con el beneficio del caso normal fijado en **$0,30**, un retraso de 500 ms ya
> consume dos tercios del margen y uno de 2 s lo supera por completo.
> **`SLIPPAGE_BUFFER = 0.01` no es un margen de seguridad: es el coste esperado
> del retraso del propio bucle.**

### 6.3 Inventario de defectos de ejecución

Ordenados por severidad.

| # | Defecto | Ubicación | Consecuencia |
|---|---|---|---|
| **B1** | **El WSS no se reconecta.** El `except` registra *"Reiniciando conexión WSS"* pero la corrutina simplemente **retorna**. `wss_task` sólo se recrea cuando cambian los tokens, es decir **una vez cada 15 minutos**. | `polymarket_wss_handler` | Si el socket cae a T-170 s, el bot opera el resto del ciclo con `live_asks` **congelados**. Dispara contra precios que ya no existen → FOK rechazadas, o peor, compra a un precio que cree bueno. **Crítico.** |
| **B2** | **Sólo se procesan snapshots completos del libro.** El handler lee `event.get("asks")` / `event.get("bids")`; los eventos `price_change` del canal *market* llevan los cambios en `changes`, no en `asks`, y se **descartan silenciosamente**. | `polymarket_wss_handler` | El top-of-book se refresca sólo con snapshots. La decisión se toma sobre un precio potencialmente obsoleto. *(Verificar contra la versión de la API en uso.)* |
| **B3** | **Los 5 reintentos FOK usan siempre el MISMO precio límite.** `precio_limite` se calcula una vez **antes** del bucle `for intento in range(...)` y nunca se recalcula desde `live_asks`. | `_ejecutar_orden_sync` | La causa habitual de rechazo de una FOK es que el precio se movió. Reintentar 5 veces al mismo límite está **garantizado a fallar**, y consume 0,7–2,8 s. |
| **B4** | **El reintento del hedge NO revalida `combo_cost <= 0.97`.** El bucle `for intento in range(1,6)` compra `token_5m` a `live_asks.get(...)` sin ningún tope. | bucle principal, ramas `ok_15m and not ok_5m` / `ok_5m and not ok_15m` | Puede completar el combo a **$1,30 o más**, garantizando pérdida. Simulado en OP08: −$3,00 en una sola operación. |
| **B5** | **`ultimo_id_15m_comprado` no se marca cuando fallan las DOS patas.** Ninguna rama lo asigna en ese caso. | bucle principal | El ciclo vuelve a dispararse en el siguiente tick, sin backoff, potencialmente durante los 180 s enteros. |
| **B6** | **No hay idempotencia en el reenvío de órdenes.** Si `post_order` lanza una excepción por *timeout* pero la orden fue aceptada, el `except` duerme 0,1 s y **reenvía una orden idéntica**. No hay client-order-id ni reconciliación de posición tras el fallo. | `_ejecutar_orden_sync` | **Vía real de compra duplicada**: hasta 5× el tamaño previsto. |
| **B7** | **Bloqueo del bucle principal hasta 26 s.** El protocolo de emergencia (`while time.time() < fin_vela_epoch`) y el bucle de hedge (5 × `await asyncio.sleep(2.0)`) se ejecutan **dentro de `cerrojo_ciclo`**, en la corrutina principal. | bucle principal | Durante ese tiempo no hay evaluación, ni salida por consola, ni reacción a nada. |
| **B8** | **`await asyncio.sleep(10.0)` antes de colocar los TP.** | bucle principal, tras combo OK | 10 s de bloqueo total con posición abierta y sin monitorización. |
| **B9** | **`reclamar_posiciones_ganadas()` es síncrona y se llama desde el bucle async**, sin timeout. | rama `else` del bucle | Congela el event loop; si la llamada cuelga, el bot **pierde la ventana entera** de 180 s. |
| **B10** | **Los TP GTC nunca se cancelan.** `cancel_all()` sólo existe en `reconciliar_estado_inicial` (arranque). | bucle principal | Órdenes de venta a 0,99 se acumulan ciclo tras ciclo. Las shares quedan **bloqueadas en el libro**, lo que puede impedir la redención de las posiciones ganadoras. |
| **B11** | **La profundidad sólo se mide en el mejor nivel.** `parse_depth_en_mejor_precio` suma únicamente los niveles cuyo precio iguala al best ask, pero la FOK se envía a `ask + 0.01` y podría barrer varios niveles. | `es_oportunidad` | **Oportunidades válidas rechazadas** por un criterio más estricto de lo necesario. |
| **B12** | **Gamma se consulta en cada tick** aunque `clobTokenIds`, `tickSize` y `negRisk` son **constantes durante todo el ciclo**. Gamma es la API más lenta y por tanto **gobierna la cadencia del bucle**. | bucle principal | 2 peticiones inútiles por tick; hasta **6.207 peticiones HTTP por ciclo de 15 min**. Es la causa principal del retraso de detección. |
| **B13** | **Riesgo de rate-limit de Binance.** Con VPS rápido: **1.241 req/min** frente al límite de 1.200/min. | `obtener_datos_spot_y_velas` | Paradoja: **cuanto mejor es la red, antes se llega al ban 418/429.** |
| **B14** | **`fetch_json` captura toda excepción y devuelve `None`**, y la condición `if d_15m and d_5m and spot_p and ...` falla en silencio: **no se emite log ni cambia la consola**. | `fetch_json` + bucle principal | Un bot ciego es indistinguible de un bot en espera. |
| **B15** | **Se registra el precio LÍMITE, no el fill.** `_ejecutar_orden_sync` devuelve `precio_limite`; `costo_final_combo = p_15m + p_5m` y `precio_compra` del protocolo de emergencia usan ese valor. | varios | PnL, Telegram y la lógica de emergencia sesgados hasta +$0,02 por combo. |
| **B16** | **`size_matched` mal interpretado.** `float(x) if x else cantidad`: si la API devuelve `0`/vacío, se asume **la cantidad completa**. `size_final = min(size_15m, size_5m)` se calcula y **nunca se usa** (los TP usan `size_15m`/`size_5m` por separado). | `_ejecutar_orden_sync` + bucle | TP dimensionados sobre una cantidad que no se posee → rechazo o venta en corto. |
| **B17** | **La dirección no se reevalúa durante los reintentos.** Tras hasta 10 s de reintentos de hedge, se compra el mismo token aunque `delta_15m` haya cambiado de signo. | bucle principal | Cobertura en el lado equivocado. |
| **B18** | **`ejecutar_y_verificar_orden` usa siempre `EXECUTOR_LEG_A`**, incluso para vender la pata 5m en emergencia. | `ejecutar_y_verificar_orden` | Serializa contra la pata A; contradice el diseño de "concurrencia real". |
| **B19** | **`ssl=False` en el `TCPConnector`.** Los datos de Binance y Gamma viajan sin verificación de certificado. | `main` | Los deltas — de los que depende toda la decisión — son manipulables por un intermediario. |
| **B20** | **`live_asks` / `live_bids` / `live_ask_depth` nunca se limpian.** Crecen con 4 tokens nuevos cada 15 min. | global | ~384 entradas/día. Fuga lenta de memoria; sin efecto sobre la lógica (los tokens nuevos devuelven `0.0` y el filtro `0.15 < ask` los descarta). |

### 6.4 El take-profit a 0,99 destruye valor

Tras un combo completo se colocan ventas GTC a **$0,99** en **ambas** patas. Pero
la pata ganadora **liquida a $1,00** al cierre. Si el TP se ejecuta, se cobran
$0,99 en lugar de $1,00: una fuga de **$0,10 sobre 10 combos**, es decir **un
tercio del beneficio objetivo de $0,30**. En el caso de doble premio la fuga es de
$0,20 sobre un beneficio de $10,50.

El TP sólo aporta valor si se le atribuye un valor explícito a liberar el capital
unos segundos antes o a evitar el riesgo de redención. Es una decisión de negocio
—no la cambio aquí—, pero debe tomarse conscientemente.

### 6.5 Riesgo de fuente de precio

El bot calcula los deltas con **Binance** (`ticker/price` y `klines`), mientras que
el mercado liquida contra **su propio oráculo**. Sensibilidad medida
(`python3 sim_oraculo.py`) sobre configuraciones que el bot cree seguras:

| Error de open (1σ) | % de "SEGURO" que en realidad son RIESGO | P($0) media | EV medio |
|---|---|---|---|
| $0 | 0,0 % | 0,00 % | +$0,30 |
| $2 | 1,3 % | 0,46 % | +$0,25 |
| $5 | 2,9 % | 1,07 % | +$0,19 |
| $10 | 6,2 % | 2,10 % | +$0,09 |
| $20 | 11,2 % | 4,59 % | **−$0,16** |

Es un riesgo de **segundo orden** comparado con §4: con desajustes realistas de
$1–$5 el EV sigue siendo positivo, pero erosiona el margen. Dado que el beneficio
por operación es de sólo $0,30, **conviene verificar cuál es la fuente oficial de
resolución de los mercados `btc-updown`** antes de confiar en cualquier cálculo
de delta.

---

## 7. Compras incorrectas, tardías, duplicadas o incompletas

| Situación | Causa en el código | Cómo debería comportarse |
|---|---|---|
| **Compra incorrecta (lado equivocado)** | La dirección se fija con `delta_15m` en el instante de la decisión y no se reevalúa en los hasta 10 s de reintentos (**B17**). | Recalcular `delta_15m` antes de cada reintento; si el signo cambió, abortar el reintento y pasar al protocolo de emergencia. |
| **Compra incorrecta (par de riesgo)** | El filtro no compara Δ15m con Δ5m (**§3**). | Medir `ancho_banda = |Δ5m| − |Δ15m|` y registrarlo. La decisión de operar o no con banda de pérdida es del operador; el código al menos debe **calcularla y mostrarla**. |
| **Compra tardía** | Cadencia real de 145–700 ms en vez de 100 ms, gobernada por las llamadas repetidas a Gamma (**B12**); WSS potencialmente congelado (**B1**, **B2**). | Cachear los metadatos de Gamma una vez por ciclo; sacar Binance del camino crítico con su propio WSS o una task independiente; reconectar el WSS con backoff. |
| **Compra duplicada** | Reenvío tras excepción sin idempotencia (**B6**); reintento sin marcar el ciclo cuando fallan las dos patas (**B5**). | Client-order-id determinista por (ciclo, pata, intento); ante excepción, **consultar el estado de la orden antes de reenviar**; marcar `ultimo_id_15m_comprado` también cuando fallan ambas patas o aplicar un backoff explícito. |
| **Compra incompleta (pata única)** | El hedge falla 5 veces → protocolo de emergencia. | Es el comportamiento previsto. Pero el protocolo vende al bid en cuanto la variación es ≥ −10 %, lo que en la práctica significa **casi siempre inmediatamente**, realizando el spread como pérdida. Debe distinguirse "cerrar por seguridad" de "cerrar por pánico". |
| **Compra incompleta (tamaño)** | `size_matched` mal interpretado (**B16**). | Tratar `None` y `0` como cero explícito; abortar los TP si el tamaño confirmado es 0; usar `size_final` (hoy muerto) o eliminarlo. |
| **Hedge a cualquier precio** | El bucle de reintento no revalida el umbral (**B4**). | Recalcular `combo_cost` con el nuevo ask antes de cada reintento y abortar si supera `UMBRAL_MAX_COMBO`. |
| **Oportunidad perdida** | Profundidad medida sólo en el mejor nivel (**B11**); FOK reintentada al mismo precio (**B3**); bot ciego por rate-limit sin log (**B14**). | Acumular profundidad hasta el precio límite; recalcular el límite en cada reintento; registrar explícitamente cada fallo de datos. |

---

## 8. Simulación práctica con banca de USD 100

`python3 sim_banca.py`. Banca inicial **$100,00**, 10 combos por operación.

### 8.1 Libro de operaciones (determinista, cubre todos los modos)

```
OP   DESCRIPCION                        D15    D5      CLASE  ENT.15m   ENT.5m   COSTO  PAYOUT     PNL    BANCA
OP01 Config SEGURA, gana normal         +45   +20     SEGURO    $0.62    $0.33    9.50   10.00   +0.50   100.50
OP02 Config SEGURA, DOBLE PREMIO        +45   +20     SEGURO    $0.62    $0.33    9.50   20.00  +10.50   111.00
OP03 Filtro rechaza (D5 < 15)           +60    +8     SEGURO        —        —    0.00    0.00   +0.00   111.00
OP04 Config RIESGO, sale bien           +22   +55     RIESGO    $0.55    $0.40    9.50   10.00   +0.50   111.50
OP05 Config RIESGO, PERDIDA TOTAL       +22   +55     RIESGO    $0.55    $0.40    9.50    0.00   -9.50   102.00
OP06 FOK rechazado en ambas patas       +40   +25     SEGURO        —        —    0.00    0.00   +0.00   102.00
OP07 PATA UNICA -> emergencia vende     +40   +25     SEGURO    $0.60        —    6.00    5.80   -0.20   101.80
OP08 Hedge tardio SIN revalidar combo   +35   +22     SEGURO    $0.58    $0.72   13.00   10.00   -3.00    98.80
OP09 Ejecucion PARCIAL (6 de 10)        +50   +30     SEGURO    $0.64    $0.32    5.76    6.00   +0.24    99.04
OP10 Error de API en pata 5m            +30   +18     SEGURO    $0.57        —    5.70    5.50   -0.20    98.84
OP11 Senales OPUESTAS (mejor caso)      +30   -25 SEGURO-MAX    $0.60    $0.30    9.00   20.00  +11.00   109.84
OP12 Config RIESGO, PERDIDA TOTAL       -21   -60     RIESGO    $0.52    $0.42    9.40    0.00   -9.40   100.44
OP13 Combo caro, filtro rechaza         +40   +18     SEGURO        —        —    0.00    0.00   +0.00   100.44
OP14 Config SEGURA, gana normal         -50   -20     SEGURO    $0.63    $0.30    9.30   10.00   +0.70   101.14
OP15 TP 0.99 llena antes del cierre     +45   +20     SEGURO    $0.62    $0.33    9.50    9.90   +0.40   101.54
--------------------------------------------------------------------------------------------------------------
TOTAL                                                                          105.66  107.20   +1.54   101.54
```

**12 operaciones ejecutadas, 7 ganadoras y 5 perdedoras, banca final $101,54 (+1,5 %).**

Lo que revela el libro:

- Las 7 ganadoras suman **+$23,84**; las 5 perdedoras suman **−$22,30**. Todo el
  resultado depende de **dos** operaciones de doble premio (OP02 y OP11, +$21,50
  entre las dos). **Sin ellas la banca habría cerrado en $80,04.**
- **Dos pérdidas totales** (OP05 y OP12, −$18,90) borran el beneficio de
  **treinta y ocho** operaciones normales a +$0,50.
- **OP08 pierde $3,00 por un bug de ejecución**, no por la estrategia: el hedge se
  compró a $0,72 llevando el combo a $1,30, muy por encima del umbral de $0,97.
- **OP07 y OP10** muestran el coste del protocolo de emergencia: −$0,20 cada una,
  el spread realizado. Es un coste **aceptable y correcto** — el protocolo hace
  su trabajo.
- **OP15** muestra la fuga del TP: $9,90 en lugar de $10,00.

### 8.2 Monte Carlo a 4.000 ciclos (~42 días de operación continua)

**Régimen A — mercado eficiente** (los precios reflejan el valor justo, que es lo
que §4 demuestra que ocurre la mayor parte del tiempo):

```
  Ciclos con señal válida y combo aceptado ....  85
  Órdenes no llenas (FOK rechazado) ...........   9
  Pata única -> protocolo emergencia ..........   6
  Hedge tardío comprado SIN revalidar umbral ..   5
  Payout $2 (doble premio) ....................   0
  Payout $0 (pérdida total) ...................  19
  Operaciones ganadoras / perdedoras .......... 58 / 27
  BANCA FINAL ................................. $0.97   (-99.0%)
  !! Banca insuficiente para operar desde el ciclo 537
```

Evolución: `100 → 109 → 115 → 111 → 96 → 81 → 72 → 59 → 43 → 19 → 0,97`

**El 68 % de las operaciones son ganadoras y la banca se destruye igualmente.**
Ésa es la firma matemática de arriesgar $9,50 para ganar $0,50.

**Régimen B — mercado dislocado** (se asume que existen infravaloraciones reales
de 0 a 8 centavos y que el bot las captura):

```
  Ciclos con señal válida y combo aceptado .... 816
  Payout $0 (pérdida total) ...................  93
  Operaciones ganadoras / perdedoras .......... 641 / 175
  BANCA FINAL ................................. $166.64  (+66.6%)
```

**Conclusión de la simulación:** la estrategia es viable **sólo** si captura
dislocaciones reales de precio. Y su capacidad de capturarlas está limitada
justamente por los defectos del §6: WSS sin reconexión (B1), libro obsoleto (B2),
cadencia real de 145–700 ms (B12) y reintentos FOK inútiles (B3).

---

## 9. Correcciones recomendadas (sin alterar la estrategia)

Ninguna cambia la señal, la dirección, los umbrales ni el objetivo. Ordenadas por
relación impacto/esfuerzo. **No se ha implementado nada; queda a la espera de
autorización.**

**Prioridad 1 — Corregir errores que causan pérdidas directas**

1. **B4** — Revalidar `combo_cost <= UMBRAL_MAX_COMBO` antes de cada reintento de
   hedge. Es una línea y evita pérdidas de $3 por evento.
2. **B1** — Bucle de reconexión con backoff en `polymarket_wss_handler`.
3. **B3** — Recalcular `precio_limite` desde `live_asks` en cada reintento FOK.
4. **B6** — Client-order-id determinista + consulta de estado antes de reenviar
   tras una excepción.
5. **B10** — Cancelar los TP GTC pendientes antes de redimir.

**Prioridad 2 — Eliminar retrasos y bloqueos**

6. **B12** — Cachear los metadatos de Gamma una vez por ciclo. Es la mejora de
   latencia con mayor retorno: elimina la API más lenta del camino crítico.
7. **B7/B8/B9** — Sacar el protocolo de emergencia y los TP a tasks
   independientes (`asyncio.create_task`) para no bloquear el bucle; envolver
   `reclamar_posiciones_ganadas` en `run_in_executor` con timeout.
8. **B2** — Procesar también los eventos `price_change` del canal *market*.
9. **B13** — Mover Binance a WebSocket o reducir la frecuencia de los klines
   (el open sólo cambia una vez cada 5/15 minutos: **no hace falta pedirlo 500
   veces por ciclo**).

**Prioridad 3 — Observabilidad y correcciones menores**

10. **B15** — Devolver y registrar el precio de fill real, no el límite.
11. **B14** — Registrar explícitamente los fallos de datos.
12. **B16** — Tratar `size_matched` vacío como 0 y abortar los TP si es 0.
13. **B11** — Acumular profundidad hasta el precio límite, no sólo en el mejor nivel.
14. **B5** — Backoff explícito cuando fallan ambas patas.
15. **B19** — Eliminar `ssl=False`.
16. **B20** — Limpiar los diccionarios de libro al cambiar de ciclo.

**Requiere decisión del operador (no es un bug)**

- **Diagnóstico de banda.** Calcular y registrar `|Δ5m| − |Δ15m|` en cada
  evaluación. Esto **no cambia la estrategia**: sólo hace visible el riesgo que ya
  se está asumiendo. Sin autorización expresa no propongo usarlo como filtro.
- **Take-profit a 0,99** (§6.4): decidir si liberar capital unos segundos antes
  compensa ceder un tercio del beneficio objetivo.
- **Tamaño de posición.** $9,70 sobre una banca de $100 es el **9,7 % del capital
  por operación**, con un modo de fallo de pérdida total. Es una decisión de
  gestión de riesgo, no una corrección de código.
- **Fuente de resolución** (§6.5): verificar el oráculo oficial de los mercados
  `btc-updown`.

---

## 10. Cómo reproducir

```bash
cd analisis_estrategia_15v5

python3 sim_escenarios.py   # los 20 escenarios, tabla + detalle por escenario
python3 sim_barrido.py      # mapa del plano Δ15/Δ5 + selección adversa
python3 sim_banca.py        # libro de operaciones + Monte Carlo con banca $100
python3 sim_latencia.py     # modelo temporal del bucle y coste del retraso
python3 sim_oraculo.py      # sensibilidad al desajuste de fuente de precio
```

Sin dependencias externas (sólo librería estándar). `motor_estrategia.py` contiene
la lógica de decisión extraída **sin modificar**; los `sim_*.py` sólo la ejecutan.

### Supuestos del modelo

| Parámetro | Valor | Dónde cambiarlo |
|---|---|---|
| Precio de BTC | $100.000 | `sim_escenarios.SPOT_REF` |
| Volatilidad | 50 % anual → σ(180 s) = $119,5 | `sim_escenarios.VOL_ANUAL` |
| Distribución del cierre | Normal alrededor del spot | `sim_escenarios.prob_close_entre` |
| Latencias de red | 4 perfiles | `sim_latencia.PERFILES` |
| Resolución de "Up" | `close > open`; empate → Down | `motor_estrategia.liquidar_combo` |

La conclusión de §3 (clasificación seguro/riesgo) es **puramente algebraica** y no
depende de ninguno de estos supuestos. Los supuestos sólo afectan a las
*probabilidades* asignadas a cada banda, no a su existencia ni a su anchura.
