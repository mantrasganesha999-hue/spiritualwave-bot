"""
sim_oraculo.py
==============

Sensibilidad al DESAJUSTE DE FUENTE DE PRECIO.

El bot calcula delta_15m y delta_5m con datos de Binance:
    open_15m = klines(BTCUSDT, 15m, limit=1)[0][1]
    open_5m  = klines(BTCUSDT, 5m,  limit=1)[0][1]
    spot     = ticker/price(BTCUSDT)

Pero los mercados btc-updown de Polymarket liquidan contra SU PROPIO oraculo.
Si el open oficial difiere del open de Binance en 'e' dolares, toda la
clasificacion seguro/riesgo se desplaza en 'e'.

Esto importa porque el propio filtro del bot trabaja con umbrales de 15-20 USD:
una discrepancia de pocos dolares puede convertir una configuracion "SEGURA"
en una de PERDIDA TOTAL.
"""

import math
import random
from motor_estrategia import clasificar_configuracion, SHARES_A_COMPRAR
from sim_escenarios import SPOT_REF, sigma_usd, prob_close_entre

random.seed(11)


def evaluar_con_error(d15, d5, err_15m, err_5m, spot=SPOT_REF, t=180.0):
    """
    d15/d5 son los deltas que el bot CREE (calculados con Binance).
    err_15m/err_5m son las diferencias entre el open de Binance y el open oficial:
        open_oficial = open_binance + err
    -> el delta REAL frente al oraculo es d - err.
    """
    clase_creida = clasificar_configuracion(d15, d5)
    d15_real, d5_real = d15 - err_15m, d5 - err_5m
    # la DIRECCION la eligio el bot con d15 (creido), no con d15_real
    signo = 1.0 if d15 >= 0 else -1.0
    o15_real, o5_real = spot - d15_real, spot - d5_real
    sep = o5_real - o15_real
    if signo * sep < 0:
        banda0 = abs(sep)
        p0 = prob_close_entre(min(o15_real, o5_real), max(o15_real, o5_real), spot, t)
        p2 = 0.0
    else:
        banda0 = 0.0
        p0 = 0.0
        p2 = prob_close_entre(min(o15_real, o5_real), max(o15_real, o5_real), spot, t)
    clase_real = "RIESGO" if banda0 > 0 else ("NEUTRO" if abs(sep) < 1e-9 else "SEGURO")
    return clase_creida, clase_real, p0, p2, banda0


def tabla(err_max=8.0, n=200_000):
    print("=" * 104)
    print("SENSIBILIDAD AL DESAJUSTE ENTRE BINANCE Y EL ORACULO DE LIQUIDACION")
    print("=" * 104)
    print("  Casos que el bot clasifica como SEGUROS pero que en realidad tienen")
    print("  banda de PERDIDA TOTAL, en funcion del error de open (USD):")
    print()
    print(f"  {'Error open':>12}{'% SEGUROS que':>18}{'P($0) media':>15}"
          f"{'EV medio':>13}{'Banda $0':>12}")
    print(f"  {'(1 sigma)':>12}{'pasan a RIESGO':>18}{'en esos casos':>15}"
          f"{'de esos':>13}{'media':>12}")
    print("  " + "-" * 100)

    for err_sigma in (0.0, 1.0, 2.0, 5.0, 10.0, 20.0):
        seguros = 0
        volteados = 0
        sum_p0 = 0.0
        sum_banda = 0.0
        for _ in range(n // 10):
            d15 = random.gauss(0, 110)
            d5 = d15 * 0.45 + random.gauss(0, 85)
            if abs(d15) < 20 or abs(d5) < 15:
                continue
            if clasificar_configuracion(d15, d5) != "SEGURO":
                continue
            seguros += 1
            e15 = random.gauss(0, err_sigma)
            e5 = random.gauss(0, err_sigma)
            _, real, p0, p2, b0 = evaluar_con_error(d15, d5, e15, e5)
            if real == "RIESGO":
                volteados += 1
                sum_p0 += p0
                sum_banda += b0
        if seguros == 0:
            continue
        pct = volteados / seguros
        p0m = sum_p0 / volteados if volteados else 0.0
        bm = sum_banda / volteados if volteados else 0.0
        # EV: combo comprado a 0.97 creyendo que es seguro
        ev = (1.0 - p0m - 0.97) * SHARES_A_COMPRAR
        print(f"  {err_sigma:>10.0f}$ {pct:>17.1%}{p0m:>15.2%}{ev:>12.2f}${bm:>11.1f}$")

    print()
    print("  Lectura: incluso un desajuste de 2 USD entre el open de Binance y el open")
    print("  oficial voltea una fraccion apreciable de las configuraciones que el bot")
    print("  cree seguras. Los umbrales del filtro (15-20 USD) son del mismo orden de")
    print("  magnitud que el error de fuente, asi que el filtro no protege contra esto.")
    print()
    print("  Ademas: el bot usa ticker/price (ultimo trade) como 'spot', mientras que")
    print("  el open de la vela es el primer trade del intervalo. Ambos son de Binance,")
    print("  pero el mercado de Polymarket puede usar otra fuente/otro metodo (media,")
    print("  mid, oraculo agregado). VERIFICAR la fuente oficial de resolucion es")
    print("  requisito previo a confiar en cualquier calculo de delta.")
    print()


if __name__ == "__main__":
    tabla()
