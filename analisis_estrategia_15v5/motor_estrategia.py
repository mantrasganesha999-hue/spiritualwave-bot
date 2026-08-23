"""
motor_estrategia.py
===================

Extraccion FIEL (sin modificar) de la logica de decision del bot
"15 vs 5 Vers: 1.09 CONCURRENCIA REAL + FILTROS DELTA 15M / 5M".

Este modulo NO propone ninguna estrategia nueva. Reproduce, linea por linea,
las mismas condiciones que el codigo original evalua en el bucle principal,
para poder simularlas de forma determinista y sin red.

Correspondencia con el codigo original
--------------------------------------
  decidir_direccion()      <-  bloque "if delta_15m >= 0: ... else: ..."
  evaluar_oportunidad()    <-  bloque "cumple_deltas / profundidad_suficiente /
                                       es_oportunidad"
  precio_limite_fok()      <-  bloque "_ejecutar_orden_sync" (rama BUY)
  liquidar_combo()         <-  reglas de settlement de los mercados
                               btc-updown-15m / btc-updown-5m de Polymarket
"""

from dataclasses import dataclass, field
from typing import Optional

# ─── Parametros EXACTOS del bot V1.09 ────────────────────────────────────────
SEGUNDOS_EVALUACION = 180
SHARES_A_COMPRAR = 10
UMBRAL_MAX_COMBO = 0.97
PRECIO_TAKE_PROFIT = 0.99
SLIPPAGE_BUFFER = 0.01
MAX_INTENTOS_COMPRA = 5
PROFUNDIDAD_MINIMA_USD = 1.0
UMBRAL_MIN_DELTA_15M = 20.0
UMBRAL_MIN_DELTA_5M = 15.0

# Limites de precio codificados dentro de "es_oportunidad"
ASK_15M_MIN, ASK_15M_MAX = 0.15, 0.90
ASK_5M_MIN, ASK_5M_MAX = 0.02, 0.95

# Tope duro del precio limite de compra en _ejecutar_orden_sync
TOPE_PRECIO_COMPRA = 0.95


# ─── Estructuras ─────────────────────────────────────────────────────────────
@dataclass
class Mercado:
    """Estado observable en el instante de la decision (T-180s ... T-0s)."""
    spot: float
    open_15m: float
    open_5m: float
    ask_15m_yes: float
    ask_15m_no: float
    ask_5m_yes: float
    ask_5m_no: float
    # tamano (en shares) disponible en el best ask de cada token
    size_15m_yes: float = 1000.0
    size_15m_no: float = 1000.0
    size_5m_yes: float = 1000.0
    size_5m_no: float = 1000.0
    t_restante: float = 180.0

    @property
    def delta_15m(self) -> float:
        return self.spot - self.open_15m

    @property
    def delta_5m(self) -> float:
        return self.spot - self.open_5m


@dataclass
class Decision:
    delta_15m: float
    delta_5m: float
    direccion: str                 # "UP (YES)" | "DOWN (NO)"
    pata_15m: str                  # token comprado en el mercado de 15m
    pata_5m: str                   # token comprado en el mercado de 5m
    ask_15m: float
    ask_5m: float
    combo_cost: float
    cumple_deltas: bool
    cumple_rangos_precio: bool
    cumple_combo: bool
    cumple_notional: bool
    profundidad_suficiente: bool
    es_oportunidad: bool
    motivo_rechazo: str = ""
    # Diagnostico anadido por el analisis (NO existe en el codigo original)
    banda_perdida_total: float = 0.0   # ancho en USD de la zona de payout $0
    banda_doble_premio: float = 0.0    # ancho en USD de la zona de payout $2
    open_15m: float = 0.0
    open_5m: float = 0.0
    spot: float = 0.0


# ─── 1. Direccion  (identico al codigo original) ─────────────────────────────
def decidir_direccion(delta_15m: float):
    """
    Codigo original:
        if delta_15m >= 0:
            token_15m, token_5m = t_15m_yes, t_5m_no ; dir = "UP (YES)"
        else:
            token_15m, token_5m = t_15m_no, t_5m_yes ; dir = "DOWN (NO)"

    OBSERVACION CLAVE: la direccion se decide UNICAMENTE con delta_15m.
    El signo de delta_5m no interviene en ningun punto de la decision.
    """
    if delta_15m >= 0:
        return "UP (YES)", "15M_YES", "5M_NO"
    return "DOWN (NO)", "15M_NO", "5M_YES"


# ─── 2. Evaluacion de oportunidad (identico al codigo original) ──────────────
def evaluar_oportunidad(m: Mercado) -> Decision:
    d15, d5 = m.delta_15m, m.delta_5m
    direccion, pata_15m, pata_5m = decidir_direccion(d15)

    if pata_15m == "15M_YES":
        ask_15m, size_15m = m.ask_15m_yes, m.size_15m_yes
        ask_5m, size_5m = m.ask_5m_no, m.size_5m_no
    else:
        ask_15m, size_15m = m.ask_15m_no, m.size_15m_no
        ask_5m, size_5m = m.ask_5m_yes, m.size_5m_yes

    combo_cost = round(ask_15m + ask_5m, 2)

    notional_15m = ask_15m * SHARES_A_COMPRAR
    notional_5m = ask_5m * SHARES_A_COMPRAR

    # NOTA: el codigo original solo mide la profundidad del MEJOR nivel de ask.
    depth_15m = size_15m * ask_15m
    depth_5m = size_5m * ask_5m
    profundidad_suficiente = (
        depth_15m >= max(notional_15m, PROFUNDIDAD_MINIMA_USD)
        and depth_5m >= max(notional_5m, PROFUNDIDAD_MINIMA_USD)
    )

    cumple_deltas = (
        abs(d15) >= UMBRAL_MIN_DELTA_15M and abs(d5) >= UMBRAL_MIN_DELTA_5M
    )
    cumple_rangos_precio = (
        ASK_15M_MIN < ask_15m < ASK_15M_MAX and ASK_5M_MIN < ask_5m < ASK_5M_MAX
    )
    cumple_combo = combo_cost <= UMBRAL_MAX_COMBO
    cumple_notional = notional_15m >= 1.0 and notional_5m >= 1.0

    es_oportunidad = (
        cumple_deltas
        and cumple_rangos_precio
        and cumple_combo
        and cumple_notional
        and profundidad_suficiente
    )

    motivos = []
    if not cumple_deltas:
        motivos.append(
            f"delta (|{d15:+.1f}|>={UMBRAL_MIN_DELTA_15M:.0f} y "
            f"|{d5:+.1f}|>={UMBRAL_MIN_DELTA_5M:.0f})"
        )
    if not cumple_rangos_precio:
        motivos.append(f"rango precio (ask15={ask_15m:.2f}, ask5={ask_5m:.2f})")
    if not cumple_combo:
        motivos.append(f"combo {combo_cost:.2f} > {UMBRAL_MAX_COMBO:.2f}")
    if not cumple_notional:
        motivos.append("notional < $1")
    if not profundidad_suficiente:
        motivos.append("profundidad best-ask insuficiente")

    # --- Diagnostico anadido por el analisis ---------------------------------
    # open_5m - open_15m = delta_15m - delta_5m
    sep = m.open_5m - m.open_15m
    signo = 1.0 if d15 >= 0 else -1.0
    if signo * sep < 0:
        banda_perdida, banda_premio = abs(sep), 0.0
    else:
        banda_perdida, banda_premio = 0.0, abs(sep)

    return Decision(
        delta_15m=d15, delta_5m=d5, direccion=direccion,
        pata_15m=pata_15m, pata_5m=pata_5m,
        ask_15m=ask_15m, ask_5m=ask_5m, combo_cost=combo_cost,
        cumple_deltas=cumple_deltas,
        cumple_rangos_precio=cumple_rangos_precio,
        cumple_combo=cumple_combo,
        cumple_notional=cumple_notional,
        profundidad_suficiente=profundidad_suficiente,
        es_oportunidad=es_oportunidad,
        motivo_rechazo="; ".join(motivos),
        banda_perdida_total=banda_perdida,
        banda_doble_premio=banda_premio,
        open_15m=m.open_15m, open_5m=m.open_5m, spot=m.spot,
    )


# ─── 3. Precio limite realmente enviado (identico a _ejecutar_orden_sync) ────
def precio_limite_fok(precio_objetivo: float) -> float:
    p = round(precio_objetivo + SLIPPAGE_BUFFER, 2)
    return min(p, TOPE_PRECIO_COMPRA)


# ─── 4. Liquidacion del combo ────────────────────────────────────────────────
def liquidar_combo(direccion: str, close: float, open_15m: float,
                   open_5m: float) -> float:
    """
    Payout por combo (1 share de cada pata), en USD.

    Mercados btc-updown: "Up" resuelve SI  close > open ; empate -> Down.

    direccion "UP (YES)"  -> se compro 15m-UP  + 5m-DOWN
    direccion "DOWN (NO)" -> se compro 15m-DOWN + 5m-UP
    """
    up_15m = close > open_15m
    up_5m = close > open_5m
    if direccion == "UP (YES)":
        return (1.0 if up_15m else 0.0) + (0.0 if up_5m else 1.0)
    return (0.0 if up_15m else 1.0) + (1.0 if up_5m else 0.0)


def clasificar_configuracion(d15: float, d5: float) -> str:
    """
    Clasificacion analitica (no existe en el codigo). Determina si el par
    comprado es estructuralmente seguro o expuesto a payout $0.

    Riesgo de payout $0  <=>  sign(d5) == sign(d15)  y  |d5| > |d15|
    """
    if d15 == 0 and d5 == 0:
        return "NEUTRO"
    mismo_signo = (d15 >= 0) == (d5 >= 0)
    if not mismo_signo:
        return "SEGURO-MAX"          # bandas opuestas, payout minimo $1, banda $2 ancha
    if abs(d15) > abs(d5):
        return "SEGURO"              # payout minimo $1, banda $2 = |d15|-|d5|
    if abs(d15) == abs(d5):
        return "NEUTRO"              # payout exactamente $1 siempre
    return "RIESGO"                  # existe banda de payout $0 = |d5|-|d15|
