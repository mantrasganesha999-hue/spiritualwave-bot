"""
sim_escenarios.py
=================

Simulacion de TODOS los escenarios derivados de las variaciones de
Delta 15m y Delta 5m, usando la logica de decision EXACTA del bot V1.09
(importada de motor_estrategia.py, sin modificarla).

Para cada escenario reporta:
  - Delta 15m / Delta 5m
  - Senal generada por el codigo
  - Condicion que activa o rechaza la compra
  - Precio esperado de entrada vs precio limite realmente enviado
  - Costo total de la operacion
  - Resultado esperado (EV) y distribucion de payouts
"""

import math
import random
from motor_estrategia import (
    Mercado, evaluar_oportunidad, decidir_direccion, precio_limite_fok,
    liquidar_combo, clasificar_configuracion,
    SHARES_A_COMPRAR, UMBRAL_MAX_COMBO, SLIPPAGE_BUFFER,
    UMBRAL_MIN_DELTA_15M, UMBRAL_MIN_DELTA_5M,
)

random.seed(20260823)

# ─── Modelo de precio de BTC ────────────────────────────────────────────────
SPOT_REF = 100_000.0
VOL_ANUAL = 0.50            # ~50% anualizado, tipico de BTC
SEG_POR_ANIO = 365 * 24 * 3600


def sigma_usd(segundos: float, spot: float = SPOT_REF) -> float:
    """Desviacion estandar del precio en USD sobre un horizonte dado."""
    return spot * VOL_ANUAL * math.sqrt(segundos / SEG_POR_ANIO)


def norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def prob_close_entre(a: float, b: float, spot: float, segundos: float) -> float:
    """P(a < close <= b) con close ~ Normal(spot, sigma) (aprox. de GBM a 3 min)."""
    s = sigma_usd(segundos, spot)
    if s <= 0:
        return 1.0 if a < spot <= b else 0.0
    return norm_cdf((b - spot) / s) - norm_cdf((a - spot) / s)


# ─── Valor teorico del combo ────────────────────────────────────────────────
def valor_teorico_combo(d15: float, d5: float, spot: float, t_restante: float):
    """
    Devuelve (valor_justo, p_payout_2, p_payout_1, p_payout_0).

    open_15m = spot - d15 ; open_5m = spot - d5.
    Payout = 1 + [banda $2] - [banda $0]; las dos bandas nunca coexisten.
    """
    o15 = spot - d15
    o5 = spot - d5
    direccion, _, _ = decidir_direccion(d15)

    lo, hi = (o15, o5) if o15 <= o5 else (o5, o15)
    p_banda = prob_close_entre(lo, hi, spot, t_restante)

    clase = clasificar_configuracion(d15, d5)
    if clase == "RIESGO":
        p2, p0 = 0.0, p_banda
    elif clase == "NEUTRO":
        p2, p0 = 0.0, 0.0
    else:
        p2, p0 = p_banda, 0.0

    p1 = 1.0 - p2 - p0
    return 1.0 + p2 - p0, p2, p1, p0, direccion, clase


# ─── Generador de escenarios ────────────────────────────────────────────────
def construir_mercado(d15, d5, ask_15m, ask_5m, spot=SPOT_REF,
                      size=1000.0, t_restante=180.0) -> Mercado:
    """
    Construye un Mercado tal que la pata que el bot va a elegir tenga
    exactamente los asks pedidos. Las patas no elegidas se rellenan con el
    complemento (1 - ask), que es como cotiza un mercado binario.
    """
    direccion, pata15, pata5 = decidir_direccion(d15)
    if pata15 == "15M_YES":
        a15y, a15n = ask_15m, round(1.0 - ask_15m + 0.02, 2)
        a5y, a5n = round(1.0 - ask_5m + 0.02, 2), ask_5m
    else:
        a15y, a15n = round(1.0 - ask_15m + 0.02, 2), ask_15m
        a5y, a5n = ask_5m, round(1.0 - ask_5m + 0.02, 2)
    return Mercado(
        spot=spot, open_15m=spot - d15, open_5m=spot - d5,
        ask_15m_yes=a15y, ask_15m_no=a15n, ask_5m_yes=a5y, ask_5m_no=a5n,
        size_15m_yes=size, size_15m_no=size, size_5m_yes=size, size_5m_no=size,
        t_restante=t_restante,
    )


def ask_coherente(d15: float, d5: float, spot: float, t_restante: float):
    """
    Asks 'justos' que un mercado eficiente cotizaria para las dos patas que el
    bot compra, mas 1 tick de spread por lado. Sirve para responder:
    'cuando el mercado esta bien valorado, que ve el bot?'
    """
    o15, o5 = spot - d15, spot - d5
    s = sigma_usd(t_restante, spot)
    p_up15 = 1.0 - norm_cdf((o15 - spot) / s)
    p_up5 = 1.0 - norm_cdf((o5 - spot) / s)
    direccion, _, _ = decidir_direccion(d15)
    if direccion == "UP (YES)":
        justo15, justo5 = p_up15, 1.0 - p_up5
    else:
        justo15, justo5 = 1.0 - p_up15, p_up5
    # ask = valor justo + 1 tick de spread, redondeado a tick 0.01
    return (min(0.99, round(justo15 + 0.01, 2)),
            min(0.99, round(justo5 + 0.01, 2)))


# ─── Escenarios ─────────────────────────────────────────────────────────────
ESCENARIOS = [
    # (nombre, d15, d5, ask_15m, ask_5m, nota)
    ("E01 Ambos UP fuertes, 15m domina",      +45.0, +20.0, 0.62, 0.33, "config SEGURA"),
    ("E02 Ambos UP, 5m domina (peligro)",     +22.0, +55.0, 0.55, 0.40, "config RIESGO"),
    ("E03 Ambos UP en el minimo del filtro",  +20.0, +15.0, 0.58, 0.36, "SEGURA, banda $2 = 5"),
    ("E04 Ambos UP, casi identicos (5m>15m)", +20.0, +21.0, 0.57, 0.38, "RIESGO, banda $0 = 1"),
    ("E05 Senales OPUESTAS: 15m UP, 5m DOWN", +30.0, -25.0, 0.60, 0.30, "SEGURO-MAX"),
    ("E06 Senales OPUESTAS: 15m DOWN, 5m UP", -30.0, +25.0, 0.58, 0.32, "SEGURO-MAX"),
    ("E07 Ambos DOWN, 15m domina",            -50.0, -20.0, 0.63, 0.30, "config SEGURA"),
    ("E08 Ambos DOWN, 5m domina (peligro)",   -21.0, -60.0, 0.52, 0.42, "config RIESGO"),
    ("E09 Delta 15m insuficiente",            +12.0, +40.0, 0.55, 0.35, "RECHAZO por filtro 15m"),
    ("E10 Delta 5m insuficiente",             +60.0, +8.0,  0.70, 0.25, "RECHAZO por filtro 5m"),
    ("E11 Ambos deltas insuficientes",         +5.0, +3.0,  0.52, 0.45, "RECHAZO por ambos filtros"),
    ("E12 Deltas OK pero combo caro",         +40.0, +18.0, 0.66, 0.35, "RECHAZO por combo > 0.97"),
    ("E13 Deltas OK, ask 15m fuera de rango", +80.0, +30.0, 0.92, 0.05, "RECHAZO ask_15m >= 0.90"),
    ("E14 Deltas OK, ask 15m demasiado bajo", +25.0, +40.0, 0.14, 0.60, "RECHAZO ask_15m <= 0.15"),
    ("E15 Delta 15m justo en cero (>=0 -> UP)", 0.0, +30.0, 0.50, 0.40, "RECHAZO por filtro 15m"),
    ("E16 Delta 15m = -0.01 -> DOWN",         -0.01, -30.0, 0.50, 0.40, "RECHAZO por filtro 15m"),
    ("E17 Reversion violenta ya consumada",   +21.0, -80.0, 0.56, 0.20, "SEGURO-MAX, banda $2 = 101"),
    ("E18 Tendencia limpia sostenida",       +120.0, +90.0, 0.80, 0.16, "SEGURA, banda $2 = 30"),
    ("E19 Aceleracion tardia (5m>>15m)",      +25.0,+110.0, 0.60, 0.30, "RIESGO, banda $0 = 85"),
    ("E20 Combo exactamente en el umbral",    +40.0, +25.0, 0.60, 0.37, "combo = 0.97, ACEPTA"),
]


def fila(nombre, d15, d5, ask15, ask5, nota, t_restante=180.0, spot=SPOT_REF):
    m = construir_mercado(d15, d5, ask15, ask5, spot=spot, t_restante=t_restante)
    dec = evaluar_oportunidad(m)
    vt, p2, p1, p0, direccion, clase = valor_teorico_combo(d15, d5, spot, t_restante)

    lim15 = precio_limite_fok(dec.ask_15m)
    lim5 = precio_limite_fok(dec.ask_5m)

    costo_esperado = round(dec.ask_15m + dec.ask_5m, 2) * SHARES_A_COMPRAR
    costo_peor_caso = round(lim15 + lim5, 2) * SHARES_A_COMPRAR

    ev_por_combo = vt - dec.combo_cost
    ev_peor = vt - round(lim15 + lim5, 2)

    return {
        "nombre": nombre, "nota": nota, "d15": d15, "d5": d5,
        "direccion": direccion, "clase": clase,
        "pata15": dec.pata_15m, "pata5": dec.pata_5m,
        "ask15": dec.ask_15m, "ask5": dec.ask_5m,
        "lim15": lim15, "lim5": lim5,
        "combo": dec.combo_cost,
        "costo_esperado": costo_esperado, "costo_peor": costo_peor_caso,
        "acepta": dec.es_oportunidad, "rechazo": dec.motivo_rechazo,
        "banda0": dec.banda_perdida_total, "banda2": dec.banda_doble_premio,
        "p2": p2, "p1": p1, "p0": p0, "valor_teorico": vt,
        "ev_combo": ev_por_combo, "ev_peor": ev_peor,
        "ev_op": ev_por_combo * SHARES_A_COMPRAR,
        "ev_op_peor": ev_peor * SHARES_A_COMPRAR,
    }


def imprimir_tabla_escenarios(t_restante=180.0):
    print("=" * 118)
    print(f"TABLA DE ESCENARIOS  (BTC ${SPOT_REF:,.0f}  |  vol {VOL_ANUAL:.0%} anual  |  "
          f"T-{t_restante:.0f}s  |  sigma = ${sigma_usd(t_restante):.1f})")
    print("=" * 118)
    hdr = (f"{'ESCENARIO':<40}{'D15':>8}{'D5':>8}{'SENAL':>12}{'CLASE':>11}"
           f"{'COMBO':>8}{'ACEPTA':>8}{'P($0)':>8}{'EV/op':>9}")
    print(hdr)
    print("-" * 118)
    filas = []
    for e in ESCENARIOS:
        f = fila(*e, t_restante=t_restante)
        filas.append(f)
        acepta = "SI" if f["acepta"] else "NO"
        print(f"{f['nombre']:<40}{f['d15']:>+8.1f}{f['d5']:>+8.1f}"
              f"{f['direccion']:>12}{f['clase']:>11}"
              f"{f['combo']:>8.2f}{acepta:>8}{f['p0']:>7.2%}"
              f"{f['ev_op']:>+9.2f}")
    print("-" * 118)
    return filas


def detalle_escenario(f):
    print()
    print("=" * 118)
    print(f"  {f['nombre']}   [{f['nota']}]")
    print("=" * 118)
    print(f"  Delta 15m ............................ ${f['d15']:+.2f}   "
          f"(umbral minimo: ${UMBRAL_MIN_DELTA_15M:.1f})")
    print(f"  Delta 5m ............................. ${f['d5']:+.2f}   "
          f"(umbral minimo: ${UMBRAL_MIN_DELTA_5M:.1f})")
    print(f"  Senal generada por el codigo ......... {f['direccion']}  ->  "
          f"compra {f['pata15']} + {f['pata5']}")
    print(f"  Clasificacion estructural ............ {f['clase']}")
    if f["banda0"] > 0:
        print(f"    !! Banda de PERDIDA TOTAL (payout $0) de ${f['banda0']:.2f} de ancho")
    elif f["banda2"] > 0:
        print(f"    -> Banda de DOBLE PREMIO (payout $2) de ${f['banda2']:.2f} de ancho, "
              f"sin banda de perdida total")
    else:
        print("    -> Sin banda: payout exactamente $1 en todos los casos")

    if f["acepta"]:
        print(f"  Condicion que ACTIVA la compra ....... "
              f"|D15|>={UMBRAL_MIN_DELTA_15M:.0f} AND |D5|>={UMBRAL_MIN_DELTA_5M:.0f} "
              f"AND 0.15<ask15<0.90 AND 0.02<ask5<0.95 "
              f"AND combo {f['combo']:.2f}<={UMBRAL_MAX_COMBO:.2f} AND profundidad OK")
    else:
        print(f"  Condicion que RECHAZA la compra ...... {f['rechazo']}")

    print(f"  Precio ESPERADO de entrada ........... 15m ${f['ask15']:.2f} | "
          f"5m ${f['ask5']:.2f}   (combo ${f['combo']:.2f})")
    print(f"  Precio LIMITE realmente enviado ...... 15m ${f['lim15']:.2f} | "
          f"5m ${f['lim5']:.2f}   (combo peor caso ${f['lim15'] + f['lim5']:.2f})")
    print(f"  Costo total esperado ({SHARES_A_COMPRAR} combos) ...... "
          f"${f['costo_esperado']:.2f}")
    print(f"  Costo total peor caso (slippage) ..... ${f['costo_peor']:.2f}")
    print(f"  Distribucion de payout ............... "
          f"P($2)={f['p2']:.2%}  P($1)={f['p1']:.2%}  P($0)={f['p0']:.2%}")
    print(f"  Valor teorico del combo .............. ${f['valor_teorico']:.4f}")
    print(f"  RESULTADO ESPERADO (EV) .............. "
          f"${f['ev_op']:+.2f} por operacion  "
          f"(peor caso slippage: ${f['ev_op_peor']:+.2f})")
    if f["acepta"]:
        maxg = (2.0 - f['combo']) * SHARES_A_COMPRAR if f['banda2'] > 0 else \
               (1.0 - f['combo']) * SHARES_A_COMPRAR
        maxp = -f['costo_peor'] if f['banda0'] > 0 else \
               (1.0 - (f['lim15'] + f['lim5'])) * SHARES_A_COMPRAR
        print(f"  Mejor caso ........................... ${maxg:+.2f}")
        print(f"  Peor caso ............................ ${maxp:+.2f}")
        if f['banda0'] == 0:
            ratio = abs(maxp) if maxp < 0 else 0
            print(f"  Relacion riesgo/beneficio ............ "
                  f"arriesga ${f['costo_peor']:.2f} para ganar "
                  f"${(1.0 - f['combo']) * SHARES_A_COMPRAR:.2f} "
                  f"(necesita {f['costo_peor'] / (f['costo_peor'] + (1.0 - f['combo']) * SHARES_A_COMPRAR):.1%} de aciertos)")


if __name__ == "__main__":
    filas = imprimir_tabla_escenarios()
    for f in filas:
        detalle_escenario(f)
