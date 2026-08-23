"""
sim_latencia.py
===============

Modelo temporal del bucle principal del bot V1.09 tal como esta escrito.
Cuantifica la cadencia real de evaluacion, el retraso de deteccion de senal y
el tiempo total hasta que la orden llega al motor de matching.

Ruta critica por tick (codigo original, dentro de la ventana T-180s):

    await asyncio.gather(
        asyncio.gather(fetch_json(url_15m), fetch_json(url_5m)),   # Gamma x2
        obtener_datos_spot_y_velas(...)                            # Binance x3
    )
    ... evaluacion ...
    await asyncio.sleep(0.1)

Las 5 peticiones van en paralelo, pero el gather espera a la MAS LENTA.
Gamma (gamma-api.polymarket.com) es tipicamente mas lenta que Binance.
"""

import math

# Latencias tipicas desde un VPS (ida y vuelta, ms)
PERFILES = {
    "VPS optimo (mismo DC que el exchange)": dict(gamma=45, binance=25, clob=35),
    "VPS bueno (EU/US, red estable)":        dict(gamma=120, binance=70, clob=90),
    "Cloud generico / residencial":          dict(gamma=280, binance=160, clob=220),
    "Conexion pobre / lejana":               dict(gamma=600, binance=350, clob=450),
}

SLEEP_BUCLE = 0.100          # await asyncio.sleep(0.1)
SEGUNDOS_EVALUACION = 180
MAX_INTENTOS_COMPRA = 5
SLEEP_REINTENTO_FOK = 0.100  # time.sleep(0.1) dentro de _ejecutar_orden_sync
SLEEP_POST_COMBO = 10.0      # await asyncio.sleep(10.0) antes de los TP
SLEEP_REINTENTO_HEDGE = 2.0  # await asyncio.sleep(2.0) x5 en el bucle de hedge


def analizar(nombre, gamma, binance, clob):
    gamma_s, binance_s, clob_s = gamma / 1000, binance / 1000, clob / 1000

    # 1. Cadencia real del bucle
    t_datos = max(gamma_s, binance_s)          # gather espera a la mas lenta
    t_tick = t_datos + SLEEP_BUCLE
    ticks_ventana = SEGUNDOS_EVALUACION / t_tick
    req_por_min = (60 / t_tick) * 5            # 2 Gamma + 3 Binance por tick
    req_ciclo = ticks_ventana * 5

    # 2. Retraso de deteccion de senal
    #    En el peor caso la condicion se cumple justo despues de un fetch:
    #    hay que esperar un tick completo, y ademas el spot leido ya tiene
    #    gamma_s/2 de antiguedad cuando se evalua.
    retraso_medio = t_tick / 2 + binance_s / 2
    retraso_peor = t_tick + binance_s

    # 3. Tiempo desde la decision hasta que la orden llega al matching
    #    create_order (firma EIP-712, ~5-15 ms) + post_order (RTT CLOB)
    firma = 0.010
    t_orden = firma + clob_s

    # 4. Tiempo total: senal ocurre -> orden en el libro
    t_total_medio = retraso_medio + t_orden
    t_total_peor = retraso_peor + t_orden

    # 5. Coste de los reintentos FOK al MISMO precio (bug: no relee live_asks)
    t_reintentos = MAX_INTENTOS_COMPRA * (t_orden + SLEEP_REINTENTO_FOK)

    # 6. Bloqueo total del bucle si falla una pata
    t_bloqueo_hedge = 5 * (SLEEP_REINTENTO_HEDGE + t_orden + t_reintentos)

    print(f"  {nombre}")
    print(f"    Latencias: Gamma {gamma}ms | Binance {binance}ms | CLOB {clob}ms")
    print(f"    Cadencia REAL del bucle .................... {t_tick * 1000:7.0f} ms  "
          f"(el codigo 'pide' 100 ms)")
    print(f"    Ticks de evaluacion en la ventana de 180 s .. {ticks_ventana:7.0f}")
    print(f"    Peticiones HTTP por ciclo de 15 m ........... {req_ciclo:7.0f}  "
          f"({req_por_min:.0f}/min)")
    print(f"    Retraso de deteccion de senal (medio) ....... {retraso_medio * 1000:7.0f} ms")
    print(f"    Retraso de deteccion de senal (peor) ........ {retraso_peor * 1000:7.0f} ms")
    print(f"    Decision -> orden en el matching (medio) .... {t_total_medio * 1000:7.0f} ms")
    print(f"    Decision -> orden en el matching (peor) ..... {t_total_peor * 1000:7.0f} ms")
    print(f"    Reintentos FOK al MISMO precio (5x) ......... {t_reintentos * 1000:7.0f} ms "
          f"(desperdiciados: el limite nunca cambia)")
    print(f"    Bloqueo del bucle si falla una pata ......... {t_bloqueo_hedge:7.1f} s  "
          f"(5 x 2 s + reintentos, TODO dentro del cerrojo)")
    print(f"    Bloqueo tras combo OK (sleep 10 s + TP) ..... {SLEEP_POST_COMBO:7.1f} s")
    print()
    return dict(t_tick=t_tick, retraso_medio=retraso_medio, retraso_peor=retraso_peor,
                t_total_medio=t_total_medio, t_total_peor=t_total_peor,
                req_ciclo=req_ciclo)


# ─── Impacto economico del retraso ──────────────────────────────────────────
SPOT_REF = 100_000.0
VOL_ANUAL = 0.50
SEG_POR_ANIO = 365 * 24 * 3600


def mov_btc(segundos):
    """Movimiento esperado (1 sigma) de BTC en 'segundos'."""
    return SPOT_REF * VOL_ANUAL * math.sqrt(segundos / SEG_POR_ANIO)


def impacto_precio(t_retraso_s):
    """
    Traduce el retraso a movimiento de precio del token.
    Cerca del vencimiento, dP_token/dSpot ~ phi(0)/sigma_restante.
    A T-180s con sigma=$119, un token at-the-money se mueve ~0.0033 por USD de BTC.
    """
    sigma_180 = mov_btc(180)
    sensibilidad = 0.3989 / sigma_180        # d(prob)/d(spot) para token ATM
    mov = mov_btc(t_retraso_s)
    return mov, mov * sensibilidad


def tabla_impacto():
    print("=" * 100)
    print("IMPACTO ECONOMICO DEL RETRASO  (BTC $100k, vol 50%, token 15m at-the-money)")
    print("=" * 100)
    print(f"  {'Retraso':>12}{'Mov. BTC (1s)':>16}{'Mov. precio token':>20}"
          f"{'Coste 10 combos':>18}")
    print("  " + "-" * 96)
    for ms in (100, 250, 500, 1000, 2000, 5000, 10000):
        mov, dp = impacto_precio(ms / 1000)
        print(f"  {ms:>10} ms{mov:>15.1f}${dp:>19.4f}{dp * 10:>17.2f}$")
    print()
    print("  Lectura: con el bucle real a ~380 ms (perfil 'Cloud generico'), el precio")
    print("  del token puede haberse movido ~0.005-0.01 antes de que la orden llegue.")
    print("  Ese es exactamente el tamano del SLIPPAGE_BUFFER (0.01): el buffer no es")
    print("  un margen de seguridad, es el coste esperado del retraso del propio bucle.")
    print()


if __name__ == "__main__":
    print("=" * 100)
    print("MODELO TEMPORAL DEL BUCLE PRINCIPAL — bot 15vs5 V1.09")
    print("=" * 100)
    print()
    for nombre, p in PERFILES.items():
        analizar(nombre, **p)
    tabla_impacto()

    print("=" * 100)
    print("LIMITES DE TASA DE BINANCE")
    print("=" * 100)
    print("  Peso por tick: ticker/price(1) + klines 15m(2) + klines 5m(2) = 5")
    print("  Limite IP: 6000 peso/min y 1200 peticiones/min (endpoints spot)")
    for nombre, p in PERFILES.items():
        t_tick = max(p["gamma"], p["binance"]) / 1000 + SLEEP_BUCLE
        ticks_min = 60 / t_tick
        peso_min = ticks_min * 5
        req_min = ticks_min * 3          # solo las 3 de Binance
        estado = "OK" if peso_min < 6000 and req_min < 1200 else "!! RIESGO DE BAN 418/429"
        print(f"    {nombre:<40} {peso_min:6.0f} peso/min  {req_min:5.0f} req/min   {estado}")
    print()
    print("  Nota: fetch_json() captura TODA excepcion y devuelve None. Un 429/418 de")
    print("  Binance deja al bot CIEGO sin emitir ningun log ni cambiar la consola.")
    print()
