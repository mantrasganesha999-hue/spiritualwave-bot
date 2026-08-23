"""
sim_banca.py
============

Simulacion practica de banca inicial USD 100 con la estrategia V1.09 TAL COMO
ESTA IMPLEMENTADA, incluyendo los modos de fallo de ejecucion reales del codigo:

  OK_COMPLETO      ambas patas llenas a FOK
  NO_EJECUTADA     ninguna pata llena (ambos FOK rechazados) -> sin gasto
  PATA_UNICA       una pata llena, la otra falla 5 veces -> protocolo emergencia
  HEDGE_TARDIO     reintento de hedge exitoso pero SIN revalidar combo <= 0.97
                   (bug real: el bucle de reintento no vuelve a comprobar el umbral)
  PARCIAL          size_matched < size pedido (el codigo lo trata como completo
                   por el bug `float(x) if x else cantidad`)
  ERROR_API        excepcion en post_order -> pata no llena

Cada operacion reporta: precio de entrada por pata, costo total, payout y banca.
"""

import math
import random
from motor_estrategia import (
    precio_limite_fok, liquidar_combo, clasificar_configuracion,
    SHARES_A_COMPRAR, UMBRAL_MAX_COMBO, PRECIO_TAKE_PROFIT, SLIPPAGE_BUFFER,
)
from sim_escenarios import SPOT_REF, sigma_usd, valor_teorico_combo, norm_cdf

BANCA_INICIAL = 100.0


# ─── Ledger deterministico: operacion por operacion ─────────────────────────
# (nombre, d15, d5, ask15, ask5, modo, close_offset_usd)
#   close_offset_usd = movimiento del spot desde la decision hasta el cierre
LEDGER = [
    ("OP01", "Config SEGURA, gana normal",        +45, +20, 0.62, 0.33, "OK_COMPLETO",   +30),
    ("OP02", "Config SEGURA, DOBLE PREMIO",       +45, +20, 0.62, 0.33, "OK_COMPLETO",   -30),
    ("OP03", "Filtro rechaza (D5 < 15)",          +60,  +8, 0.70, 0.25, "NO_EVALUADA",     0),
    ("OP04", "Config RIESGO, sale bien",          +22, +55, 0.55, 0.40, "OK_COMPLETO",   +40),
    ("OP05", "Config RIESGO, PERDIDA TOTAL",      +22, +55, 0.55, 0.40, "OK_COMPLETO",   -35),
    ("OP06", "FOK rechazado en ambas patas",      +40, +25, 0.60, 0.37, "NO_EJECUTADA",  +20),
    ("OP07", "PATA UNICA -> emergencia vende",    +40, +25, 0.60, 0.37, "PATA_UNICA",    +20),
    ("OP08", "Hedge tardio SIN revalidar combo",  +35, +22, 0.58, 0.36, "HEDGE_TARDIO",  +25),
    ("OP09", "Ejecucion PARCIAL (6 de 10)",       +50, +30, 0.64, 0.32, "PARCIAL",       +40),
    ("OP10", "Error de API en pata 5m",           +30, +18, 0.57, 0.38, "ERROR_API",     +10),
    ("OP11", "Senales OPUESTAS (mejor caso)",     +30, -25, 0.60, 0.30, "OK_COMPLETO",   -10),
    ("OP12", "Config RIESGO, PERDIDA TOTAL",      -21, -60, 0.52, 0.42, "OK_COMPLETO",   +45),
    ("OP13", "Combo caro, filtro rechaza",        +40, +18, 0.66, 0.35, "NO_EVALUADA",     0),
    ("OP14", "Config SEGURA, gana normal",        -50, -20, 0.63, 0.30, "OK_COMPLETO",   -40),
    ("OP15", "TP 0.99 llena antes del cierre",    +45, +20, 0.62, 0.33, "OK_TP",         +60),
]


def ejecutar_operacion(banca, cod, desc, d15, d5, ask15, ask5, modo, close_off,
                       shares=SHARES_A_COMPRAR, spot=SPOT_REF):
    """Devuelve dict con el detalle contable de una operacion."""
    from motor_estrategia import decidir_direccion
    direccion, pata15, pata5 = decidir_direccion(d15)
    o15, o5 = spot - d15, spot - d5
    close = spot + close_off
    clase = clasificar_configuracion(d15, d5)

    lim15 = precio_limite_fok(ask15)
    lim5 = precio_limite_fok(ask5)
    combo_visto = round(ask15 + ask5, 2)

    r = {"cod": cod, "desc": desc, "d15": d15, "d5": d5, "modo": modo,
         "direccion": direccion, "clase": clase,
         "combo_visto": combo_visto, "shares": shares,
         "p15": None, "p5": None, "costo": 0.0, "payout": 0.0,
         "close": close, "o15": o15, "o5": o5, "nota": ""}

    if modo in ("NO_EVALUADA", "NO_EJECUTADA"):
        if modo == "NO_EVALUADA":
            r["nota"] = ("Filtro rechaza: no se envia ninguna orden. "
                         "Sin gasto ni riesgo.")
        else:
            r["nota"] = (f"5 intentos FOK por pata al MISMO precio limite "
                         f"(${lim15:.2f}/${lim5:.2f}); el libro ya se habia movido. "
                         f"Sin gasto, oportunidad perdida.")
        r["pnl"] = 0.0
        r["banca"] = banca
        return r

    # Precio de ejecucion: FOK marketable casa contra el ask en libro.
    # Peor caso (libro movido dentro del buffer) = precio limite.
    p15_fill = ask15
    p5_fill = ask5

    if modo == "OK_COMPLETO" or modo == "OK_TP":
        r["p15"], r["p5"] = p15_fill, p5_fill
        r["costo"] = round((p15_fill + p5_fill) * shares, 2)
        payout_unit = liquidar_combo(direccion, close, o15, o5)
        if modo == "OK_TP":
            # TP GTC a 0.99: la pata ganadora se vende a 0.99 en vez de liquidar a 1.00
            payout_unit_tp = 0.0
            if payout_unit >= 1:
                payout_unit_tp += PRECIO_TAKE_PROFIT
            if payout_unit >= 2:
                payout_unit_tp += PRECIO_TAKE_PROFIT
            r["payout"] = round(payout_unit_tp * shares, 2)
            r["nota"] = (f"Payout de liquidacion habria sido ${payout_unit * shares:.2f}; "
                         f"el TP a $0.99 lo reduce a ${r['payout']:.2f} "
                         f"(fuga de ${payout_unit * shares - r['payout']:.2f}).")
        else:
            r["payout"] = round(payout_unit * shares, 2)
            if payout_unit == 0:
                r["nota"] = (f"PERDIDA TOTAL: close ${close:,.0f} cayo dentro de la banda "
                             f"[{min(o15, o5):,.0f}, {max(o15, o5):,.0f}] de ancho "
                             f"${abs(o5 - o15):.0f}. Config {clase}.")
            elif payout_unit == 2:
                r["nota"] = (f"DOBLE PREMIO: close ${close:,.0f} dentro de la banda "
                             f"[{min(o15, o5):,.0f}, {max(o15, o5):,.0f}]. Ambas patas ganan.")
            else:
                r["nota"] = "Resultado normal: gana una pata, la otra expira sin valor."

    elif modo == "PATA_UNICA":
        # Pata 15m llena, pata 5m falla 5 veces (10 s de reintentos), luego
        # protocolo de emergencia vende al bid. Bid tipico = ask - 1 tick.
        p15_fill = lim15          # el codigo registra el LIMITE, no el fill real
        bid_venta = round(ask15 - 0.02, 2)
        r["p15"], r["p5"] = ask15, None
        r["costo"] = round(ask15 * shares, 2)
        r["payout"] = round(bid_venta * shares, 2)
        r["nota"] = (f"Pata 5m nunca se lleno. 5 reintentos x 2s = 10s de bloqueo "
                     f"del bucle principal. Emergencia vende la pata 15m al bid "
                     f"${bid_venta:.2f} (var {(bid_venta - ask15) / ask15:+.1%} >= -10%). "
                     f"Perdida = spread.")

    elif modo == "HEDGE_TARDIO":
        # Bug: el bucle de reintento compra el hedge a `live_asks` actual SIN
        # volver a validar combo <= UMBRAL_MAX_COMBO.
        ask5_tardio = 0.72        # el mercado se movio en los 10 s de reintentos
        r["p15"], r["p5"] = ask15, ask5_tardio
        r["costo"] = round((ask15 + ask5_tardio) * shares, 2)
        payout_unit = liquidar_combo(direccion, close, o15, o5)
        r["payout"] = round(payout_unit * shares, 2)
        r["nota"] = (f"Combo real ${ask15 + ask5_tardio:.2f} > umbral "
                     f"${UMBRAL_MAX_COMBO:.2f}. El reintento NO revalida el umbral: "
                     f"compra garantizando perdida si el payout es $1.")

    elif modo == "PARCIAL":
        llenos = 6
        r["p15"], r["p5"] = ask15, ask5
        r["costo"] = round((ask15 + ask5) * llenos, 2)
        payout_unit = liquidar_combo(direccion, close, o15, o5)
        r["payout"] = round(payout_unit * llenos, 2)
        r["shares"] = llenos
        r["nota"] = (f"Solo {llenos}/{shares} combos llenos. El codigo hace "
                     f"`float(x) if x else cantidad`: si size_matched llega vacio "
                     f"asume {shares} y coloca TP por {shares} -> TP sobredimensionado.")

    elif modo == "ERROR_API":
        r["p15"], r["p5"] = ask15, None
        r["costo"] = round(ask15 * shares, 2)
        bid_venta = round(ask15 - 0.02, 2)
        r["payout"] = round(bid_venta * shares, 2)
        r["nota"] = ("Excepcion en post_order de la pata 5m; se agotan los 5 intentos. "
                     "Queda pata unica -> emergencia. Mismo coste que PATA_UNICA.")

    r["pnl"] = round(r["payout"] - r["costo"], 2)
    r["banca"] = round(banca + r["pnl"], 2)
    return r


def correr_ledger():
    print("=" * 122)
    print(f"SIMULACION PRACTICA — BANCA INICIAL ${BANCA_INICIAL:.2f} USD  |  "
          f"{SHARES_A_COMPRAR} combos/operacion  |  BTC ${SPOT_REF:,.0f}")
    print("=" * 122)
    hdr = (f"{'OP':<5}{'DESCRIPCION':<32}{'D15':>6}{'D5':>6}{'CLASE':>11}"
           f"{'ENT.15m':>9}{'ENT.5m':>9}{'COSTO':>8}{'PAYOUT':>8}{'PNL':>8}{'BANCA':>9}")
    print(hdr)
    print("-" * 122)
    banca = BANCA_INICIAL
    filas = []
    for cod, desc, d15, d5, a15, a5, modo, off in LEDGER:
        r = ejecutar_operacion(banca, cod, desc, d15, d5, a15, a5, modo, off)
        banca = r["banca"]
        filas.append(r)
        e15 = f"${r['p15']:.2f}" if r["p15"] is not None else "—"
        e5 = f"${r['p5']:.2f}" if r["p5"] is not None else "—"
        print(f"{r['cod']:<5}{r['desc']:<32}{r['d15']:>+6.0f}{r['d5']:>+6.0f}"
              f"{r['clase']:>11}{e15:>9}{e5:>9}"
              f"{r['costo']:>8.2f}{r['payout']:>8.2f}{r['pnl']:>+8.2f}{r['banca']:>9.2f}")
    print("-" * 122)
    pnl_total = round(banca - BANCA_INICIAL, 2)
    ejec = [f for f in filas if f["costo"] > 0]
    gan = [f for f in ejec if f["pnl"] > 0]
    per = [f for f in ejec if f["pnl"] < 0]
    print(f"{'TOTAL':<5}{'':<32}{'':>6}{'':>6}{'':>11}{'':>9}{'':>9}"
          f"{sum(f['costo'] for f in filas):>8.2f}"
          f"{sum(f['payout'] for f in filas):>8.2f}"
          f"{pnl_total:>+8.2f}{banca:>9.2f}")
    print()
    print(f"  Operaciones totales evaluadas ........ {len(filas)}")
    print(f"  Ejecutadas (con gasto real) .......... {len(ejec)}")
    print(f"  No ejecutadas / rechazadas ........... {len(filas) - len(ejec)}")
    print(f"  Ganadoras ............................ {len(gan)}  "
          f"(suma ${sum(f['pnl'] for f in gan):+.2f})")
    print(f"  Perdedoras ........................... {len(per)}  "
          f"(suma ${sum(f['pnl'] for f in per):+.2f})")
    print(f"  Banca final .......................... ${banca:.2f}  "
          f"({(banca / BANCA_INICIAL - 1):+.1%})")
    print()
    print("  NOTAS POR OPERACION")
    print("  " + "-" * 118)
    for f in filas:
        print(f"  {f['cod']} [{f['modo']:<13}] {f['nota']}")
    print()
    return filas


# ─── Monte Carlo: que pasa a lo largo de muchos ciclos ──────────────────────
def monte_carlo(n_ciclos=4000, semilla=7, regimen="eficiente",
                p_fok_falla=0.25, p_una_pata=0.12, p_hedge_tardio=0.35,
                banca0=BANCA_INICIAL, shares=SHARES_A_COMPRAR, verbose=True):
    """
    regimen "eficiente"  : el mercado cotiza a valor justo -> el filtro solo deja
                           pasar configuraciones de RIESGO (ver sim_barrido.py).
    regimen "dislocado"  : se asume que existen combos infravalorados y que el
                           bot captura una mezcla 50/50 seguro/riesgo.
    """
    rnd = random.Random(semilla)
    banca = banca0
    hist = []
    n_trade = n_win = n_loss = n_zero = n_double = 0
    n_nofill = n_unaleg = n_hedgetardio = 0
    ruina = None

    for i in range(n_ciclos):
        # --- generar un ciclo con deltas plausibles ---
        d15 = rnd.gauss(0, 110)      # deriva de 15 min
        d5 = d15 * 0.45 + rnd.gauss(0, 85)   # los 5m correlacionan parcialmente
        if abs(d15) < 20 or abs(d5) < 15:
            hist.append(("SIN_SENAL", 0.0, banca))
            continue

        clase = clasificar_configuracion(d15, d5)
        vt, p2, p1, p0, direccion, _ = valor_teorico_combo(d15, d5, SPOT_REF, 180.0)

        if regimen == "eficiente":
            # ask = valor justo + 1 tick por pata; el combo solo baja de 0.97
            # cuando vt < ~0.99, es decir en configuraciones de RIESGO
            combo = round(vt + 0.02, 2)
        else:
            # dislocacion: descuento aleatorio de 0 a 8 centavos
            combo = round(vt + 0.02 - rnd.uniform(0.0, 0.08), 2)

        if combo > UMBRAL_MAX_COMBO or combo < 0.30:
            hist.append(("RECHAZADA", 0.0, banca))
            continue
        if banca < combo * shares:
            hist.append(("SIN_FONDOS", 0.0, banca))
            continue

        n_trade += 1

        # --- modelo de ejecucion ---
        u = rnd.random()
        if u < p_fok_falla * 0.35:
            n_nofill += 1
            hist.append(("NO_FILL", 0.0, banca))
            n_trade -= 1
            continue

        costo_unit = combo
        if u < p_fok_falla * 0.35 + p_una_pata:
            # una pata sola; con prob p_hedge_tardio el hedge entra caro
            if rnd.random() < p_hedge_tardio:
                n_hedgetardio += 1
                costo_unit = combo + rnd.uniform(0.05, 0.30)   # hedge sin revalidar
            else:
                n_unaleg += 1
                # emergencia: vende al bid, pierde el spread (~2 ticks)
                pnl = -0.02 * shares
                banca = round(banca + pnl, 2)
                n_loss += 1
                hist.append(("PATA_UNICA", pnl, banca))
                continue

        # --- liquidacion ---
        r = rnd.random()
        if r < p0:
            payout_unit = 0.0
            n_zero += 1
        elif r < p0 + p2:
            payout_unit = 2.0
            n_double += 1
        else:
            payout_unit = 1.0

        pnl = round((payout_unit - costo_unit) * shares, 2)
        banca = round(banca + pnl, 2)
        if pnl > 0:
            n_win += 1
        elif pnl < 0:
            n_loss += 1
        hist.append(("TRADE", pnl, banca))

        if banca < combo * shares and ruina is None:
            ruina = i

    if verbose:
        print("=" * 100)
        print(f"MONTE CARLO — regimen '{regimen}'  |  {n_ciclos} ciclos de 15m "
              f"(~{n_ciclos * 15 / 60 / 24:.0f} dias)  |  banca inicial ${banca0:.2f}")
        print("=" * 100)
        print(f"  Ciclos con senal valida y combo aceptado .... {n_trade}")
        print(f"  Ordenes no llenas (FOK rechazado) ........... {n_nofill}")
        print(f"  Pata unica -> protocolo emergencia .......... {n_unaleg}")
        print(f"  Hedge tardio comprado SIN revalidar umbral .. {n_hedgetardio}")
        print(f"  Payout $2 (doble premio) .................... {n_double}")
        print(f"  Payout $0 (perdida total) ................... {n_zero}")
        print(f"  Operaciones ganadoras / perdedoras .......... {n_win} / {n_loss}")
        print(f"  BANCA FINAL ................................. ${banca:.2f}  "
              f"({(banca / banca0 - 1):+.1%})")
        if ruina is not None:
            print(f"  !! Banca insuficiente para operar a partir del ciclo {ruina}")
        print()
    return banca, hist


def curva_banca(hist, banca0, n=None):
    """Imprime la evolucion de la banca cada 250 operaciones ejecutadas."""
    print("  Evolucion de banca (solo ciclos con operacion ejecutada):")
    ejec = [h for h in hist if h[0] in ("TRADE", "PATA_UNICA")]
    if not ejec:
        print("    (ninguna)")
        return
    paso = max(1, len(ejec) // 12)
    print(f"    {'op#':>6}{'banca':>12}")
    for i in range(0, len(ejec), paso):
        print(f"    {i:>6}{ejec[i][2]:>12.2f}")
    print(f"    {len(ejec) - 1:>6}{ejec[-1][2]:>12.2f}")
    print()


if __name__ == "__main__":
    correr_ledger()
    for reg in ("eficiente", "dislocado"):
        b, h = monte_carlo(regimen=reg)
        curva_banca(h, BANCA_INICIAL)
