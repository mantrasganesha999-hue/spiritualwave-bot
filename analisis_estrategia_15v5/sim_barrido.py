"""
sim_barrido.py
==============

Barrido exhaustivo del plano (Delta 15m, Delta 5m) con la logica de decision
EXACTA del bot V1.09, respondiendo dos preguntas:

  A) Cuando el mercado cotiza a VALOR JUSTO, que combinaciones de deltas deja
     pasar el filtro `combo_cost <= 0.97`?  -> mide SELECCION ADVERSA.

  B) Cual es el EV de cada combinacion aceptada, y que fraccion del espacio
     aceptado es estructuralmente perdedora?
"""

import math
from motor_estrategia import (
    Mercado, evaluar_oportunidad, decidir_direccion, precio_limite_fok,
    clasificar_configuracion, SHARES_A_COMPRAR, UMBRAL_MAX_COMBO,
    UMBRAL_MIN_DELTA_15M, UMBRAL_MIN_DELTA_5M,
)
from sim_escenarios import (
    SPOT_REF, sigma_usd, norm_cdf, valor_teorico_combo, ask_coherente,
    construir_mercado,
)


def barrido(t_restante=180.0, paso=5.0, rango=150.0):
    """Recorre d15 y d5 en [-rango, rango] con asks de mercado eficiente."""
    vals = [v for v in frange(-rango, rango, paso)]
    aceptados = []
    rechazados_por_delta = 0
    rechazados_por_combo = 0
    rechazados_por_rango = 0
    total = 0

    for d15 in vals:
        for d5 in vals:
            total += 1
            a15, a5 = ask_coherente(d15, d5, SPOT_REF, t_restante)
            m = construir_mercado(d15, d5, a15, a5, spot=SPOT_REF,
                                  t_restante=t_restante)
            dec = evaluar_oportunidad(m)
            vt, p2, p1, p0, direccion, clase = valor_teorico_combo(
                d15, d5, SPOT_REF, t_restante)

            if not dec.cumple_deltas:
                rechazados_por_delta += 1
                continue
            if not dec.cumple_rangos_precio:
                rechazados_por_rango += 1
                continue
            if not dec.cumple_combo:
                rechazados_por_combo += 1
                continue

            lim = precio_limite_fok(dec.ask_15m) + precio_limite_fok(dec.ask_5m)
            aceptados.append({
                "d15": d15, "d5": d5, "clase": clase, "combo": dec.combo_cost,
                "combo_lim": round(lim, 2), "p0": p0, "p2": p2, "vt": vt,
                "ev": (vt - dec.combo_cost) * SHARES_A_COMPRAR,
                "ev_lim": (vt - round(lim, 2)) * SHARES_A_COMPRAR,
            })
    return aceptados, total, rechazados_por_delta, rechazados_por_rango, rechazados_por_combo


def frange(a, b, step):
    x = a
    out = []
    while x <= b + 1e-9:
        out.append(round(x, 4))
        x += step
    return out


def informe():
    for t in (180.0, 90.0, 30.0, 5.0):
        acep, total, rd, rr, rc = barrido(t_restante=t)
        print("=" * 100)
        print(f"BARRIDO con mercado EFICIENTE  |  T-{t:.0f}s  |  "
              f"sigma = ${sigma_usd(t):.1f}  |  {total} combinaciones (d15,d5) en [-150,+150] paso 5")
        print("=" * 100)
        print(f"  Rechazados por filtro de DELTA ....... {rd:5d}  ({rd/total:.1%})")
        print(f"  Rechazados por rango de precio ....... {rr:5d}  ({rr/total:.1%})")
        print(f"  Rechazados por combo > 0.97 .......... {rc:5d}  ({rc/total:.1%})")
        print(f"  ACEPTADOS (dispara compra) ........... {len(acep):5d}  ({len(acep)/total:.1%})")
        if not acep:
            print("  -> Ninguna combinacion pasa el filtro a precios justos.\n")
            continue

        riesgo = [a for a in acep if a["clase"] == "RIESGO"]
        seguro = [a for a in acep if a["clase"] in ("SEGURO", "SEGURO-MAX")]
        neutro = [a for a in acep if a["clase"] == "NEUTRO"]
        ev_medio = sum(a["ev"] for a in acep) / len(acep)
        ev_medio_lim = sum(a["ev_lim"] for a in acep) / len(acep)
        negativos = [a for a in acep if a["ev"] < 0]

        print(f"  De los aceptados:")
        print(f"     config RIESGO  (existe payout $0) . {len(riesgo):5d}  ({len(riesgo)/len(acep):.1%})")
        print(f"     config SEGURA  (payout minimo $1) . {len(seguro):5d}  ({len(seguro)/len(acep):.1%})")
        print(f"     config NEUTRA  (payout siempre $1)  {len(neutro):5d}  ({len(neutro)/len(acep):.1%})")
        print(f"     con EV NEGATIVO ................... {len(negativos):5d}  ({len(negativos)/len(acep):.1%})")
        print(f"  EV medio por operacion ............... ${ev_medio:+.3f}")
        print(f"  EV medio con slippage +0.01/pata ..... ${ev_medio_lim:+.3f}")
        peor = min(acep, key=lambda a: a["ev"])
        mejor = max(acep, key=lambda a: a["ev"])
        print(f"  Peor  aceptado: d15={peor['d15']:+.0f} d5={peor['d5']:+.0f} "
              f"clase={peor['clase']} combo={peor['combo']:.2f} "
              f"P($0)={peor['p0']:.1%} EV=${peor['ev']:+.2f}")
        print(f"  Mejor aceptado: d15={mejor['d15']:+.0f} d5={mejor['d5']:+.0f} "
              f"clase={mejor['clase']} combo={mejor['combo']:.2f} "
              f"P($2)={mejor['p2']:.1%} EV=${mejor['ev']:+.2f}")
        print()


def mapa_clases(t_restante=180.0):
    """Mapa visual: para cada (d15,d5) que pasa el filtro de DELTA, su clase."""
    print("=" * 100)
    print("MAPA DE CLASES ESTRUCTURALES sobre el espacio que el FILTRO DE DELTA aprueba")
    print("  (filas = Delta 15m, columnas = Delta 5m, paso 10 USD)")
    print("  '.' = rechazado por filtro delta   'S' = SEGURO   'X' = RIESGO ($0 posible)   '=' = NEUTRO")
    print("=" * 100)
    vals = frange(-60, 60, 10)
    print("  d15\\d5 " + "".join(f"{int(v):>5}" for v in vals))
    for d15 in vals:
        fila = f"{int(d15):>7} "
        for d5 in vals:
            if abs(d15) < UMBRAL_MIN_DELTA_15M or abs(d5) < UMBRAL_MIN_DELTA_5M:
                fila += f"{'.':>5}"
            else:
                c = clasificar_configuracion(d15, d5)
                s = {"RIESGO": "X", "SEGURO": "S", "SEGURO-MAX": "S",
                     "NEUTRO": "="}[c]
                fila += f"{s:>5}"
        print(fila)
    print()

    # cuantificacion
    vals_f = frange(-150, 150, 1)
    aprobados = 0
    riesgo = 0
    for d15 in vals_f:
        for d5 in vals_f:
            if abs(d15) >= UMBRAL_MIN_DELTA_15M and abs(d5) >= UMBRAL_MIN_DELTA_5M:
                aprobados += 1
                if clasificar_configuracion(d15, d5) == "RIESGO":
                    riesgo += 1
    print(f"  Sobre la rejilla completa [-150,+150] paso 1 USD:")
    print(f"    combinaciones que el FILTRO DE DELTA aprueba .... {aprobados}")
    print(f"    de esas, estructuralmente de RIESGO (payout $0) . {riesgo}  "
          f"({riesgo/aprobados:.1%})")
    print(f"  -> El filtro de delta NO discrimina entre configuracion segura y de riesgo.")
    print()


if __name__ == "__main__":
    mapa_clases()
    informe()
