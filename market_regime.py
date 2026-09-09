# ============================================================
# WILL STREEP - MARKET REGIME AUTONOMO V3
# Version GitHub Actions
# ============================================================

import os
from datetime import datetime
from zoneinfo import ZoneInfo

import yfinance as yf
import pandas as pd
import numpy as np


# ============================================================
# CONFIGURACION
# ============================================================

TICKERS = {
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "XAUUSD": "GC=F",
    "NASDAQ": "QQQ",
    "SP500": "SPY",
    "USD": "UUP",
    "VIX": "^VIX",
    "BONDS": "IEF"
}

SENSORES = ["USD", "NASDAQ", "SP500", "VIX", "BONDS"]

ARCHIVO_HISTORIAL = "market_regime_historial.csv"


# ============================================================
# 1. DESCARGAR HISTORICO
# ============================================================

print("Preparando histórico para calibrar el sistema...")

historico = {}

for nombre in SENSORES:

    ticker = TICKERS[nombre]

    df = yf.download(
        ticker,
        period="2y",
        interval="1h",
        auto_adjust=True,
        progress=False
    )

    if df.empty:
        raise ValueError(
            f"No se pudo descargar histórico de {nombre}"
        )

    close = df["Close"]

    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]

    close = close.dropna()

    retornos = close.pct_change(
        fill_method=None
    ) * 100

    retornos = retornos.replace(
        [np.inf, -np.inf],
        np.nan
    ).dropna()

    historico[nombre] = retornos

    print(
        nombre,
        "->",
        len(retornos),
        "observaciones"
    )

print("\nCALIBRACION COMPLETA ✓")


# ============================================================
# 2. SCORE HISTORICO 0-100
# ============================================================

def calcular_score(sensor, cambio):

    h = historico[sensor].dropna()

    score = (h <= cambio).mean() * 100

    return round(float(score), 1)


def clasificar(score):

    if score >= 80:
        return "MUY FUERTE ↑↑"

    elif score >= 65:
        return "FUERTE ↑"

    elif score <= 20:
        return "MUY DEBIL ↓↓"

    elif score <= 35:
        return "DEBIL ↓"

    else:
        return "NEUTRO →"


# ============================================================
# 3. DESCARGAR MERCADO ACTUAL
# ============================================================

def descargar_actual():

    datos = {}

    for nombre, ticker in TICKERS.items():

        df = yf.download(
            ticker,
            period="5d",
            interval="1h",
            auto_adjust=True,
            progress=False
        )

        if df.empty:
            raise ValueError(
                f"No llegaron datos actuales de {nombre}"
            )

        close = df["Close"]

        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]

        close = close.dropna()

        if len(close) < 2:
            raise ValueError(
                f"Datos insuficientes de {nombre}"
            )

        cambio = (
            close.pct_change(fill_method=None).iloc[-1]
            * 100
        )

        datos[nombre] = {
            "precio": float(close.iloc[-1]),
            "cambio": float(cambio),
            "ultima_vela": close.index[-1]
        }

    return datos


# ============================================================
# 4. MARKET REGIME
# ============================================================

def ejecutar_market_regime():

    hora = datetime.now(
        ZoneInfo("America/La_Paz")
    )

    datos = descargar_actual()

    scores = {}

    for sensor in SENSORES:

        scores[sensor] = calcular_score(
            sensor,
            datos[sensor]["cambio"]
        )

    # ========================================================
    # USD
    # ========================================================

    usd = scores["USD"]


    # ========================================================
    # EURUSD
    # Resultados del TEST que obtuvimos en Colab
    # ========================================================

    if usd >= 80:

        eur_bias = "BAJISTA"
        eur_prob = 69.23

    elif usd <= 20:

        eur_bias = "ALCISTA"
        eur_prob = 67.65

    else:

        eur_bias = "NEUTRO"
        eur_prob = None


    # ========================================================
    # GBPUSD
    # ========================================================

    if usd >= 80:

        gbp_bias = "BAJISTA"
        gbp_prob = 71.79

    elif usd <= 20:

        gbp_bias = "ALCISTA"
        gbp_prob = 64.71

    else:

        gbp_bias = "NEUTRO"
        gbp_prob = None


    # ========================================================
    # RISK SCORE
    # ========================================================

    risk_score = round(
        (
            scores["NASDAQ"]
            + scores["SP500"]
            + (100 - scores["VIX"])
        ) / 3,
        1
    )

    if risk_score >= 65:
        risk_estado = "RISK-ON"

    elif risk_score <= 35:
        risk_estado = "RISK-OFF"

    else:
        risk_estado = "NEUTRO"


    # ========================================================
    # GOLD SCORE EXPERIMENTAL
    # ========================================================

    gold_score = round(
        (
            (100 - scores["USD"])
            + scores["VIX"]
            + scores["BONDS"]
        ) / 3,
        1
    )

    if gold_score >= 65:
        gold_bias = "ALCISTA"

    elif gold_score <= 35:
        gold_bias = "BAJISTA"

    else:
        gold_bias = "MIXTO"


    # ========================================================
    # DASHBOARD
    # ========================================================

    print("\n")
    print("=" * 70)
    print("          WILL STREEP - MARKET REGIME")
    print("=" * 70)

    print(
        "Hora Bolivia:",
        hora.strftime("%Y-%m-%d %H:%M:%S")
    )

    print("\nSENSORES INTERMERCADO")
    print("-" * 70)

    for sensor in SENSORES:

        print(
            f"{sensor:8}",
            f"{scores[sensor]:5.1f}/100",
            f"{clasificar(scores[sensor]):16}",
            f"Cambio {datos[sensor]['cambio']:+.3f}%"
        )


    print("\n" + "=" * 70)
    print("REGIMEN GLOBAL")
    print("=" * 70)

    print(
        f"USD STRENGTH : "
        f"{usd:5.1f}/100   "
        f"{clasificar(usd)}"
    )

    print(
        f"RISK SCORE   : "
        f"{risk_score:5.1f}/100   "
        f"{risk_estado}"
    )

    print(
        f"GOLD SCORE   : "
        f"{gold_score:5.1f}/100   "
        f"{gold_bias}"
    )


    # ========================================================
    # CONTEXTO OPERATIVO
    # ========================================================

    print("\n" + "=" * 70)
    print("CONTEXTO OPERATIVO")
    print("=" * 70)


    print("\nEURUSD")
    print("Bias:", eur_bias)

    if eur_prob is not None:

        print(
            "Referencia histórica TEST:",
            eur_prob,
            "%"
        )

    else:

        print(
            "Referencia histórica TEST: SIN SEÑAL"
        )


    print("\nGBPUSD")
    print("Bias:", gbp_bias)

    if gbp_prob is not None:

        print(
            "Referencia histórica TEST:",
            gbp_prob,
            "%"
        )

    else:

        print(
            "Referencia histórica TEST: SIN SEÑAL"
        )


    print("\nXAUUSD")

    print(
        "Bias:",
        gold_bias
    )

    print(
        "Score:",
        gold_score,
        "/100"
    )

    print(
        "Modelo: EXPERIMENTAL"
    )


    # ========================================================
    # ULTIMAS VELAS
    # ========================================================

    print("\n" + "-" * 70)

    print(
        "ULTIMA VELA RECIBIDA"
    )

    for sensor in SENSORES:

        print(
            f"{sensor:8}",
            datos[sensor]["ultima_vela"]
        )


    # ========================================================
    # GUARDAR HISTORIAL
    # ========================================================

    nueva_lectura = {

        "FECHA_BOLIVIA":
            hora.strftime("%Y-%m-%d %H:%M:%S"),

        "USD":
            scores["USD"],

        "NASDAQ":
            scores["NASDAQ"],

        "SP500":
            scores["SP500"],

        "VIX":
            scores["VIX"],

        "BONDS":
            scores["BONDS"],

        "RISK_SCORE":
            risk_score,

        "RISK_REGIME":
            risk_estado,

        "EURUSD":
            eur_bias,

        "EUR_PROB":
            eur_prob,

        "GBPUSD":
            gbp_bias,

        "GBP_PROB":
            gbp_prob,

        "GOLD_SCORE":
            gold_score,

        "XAUUSD":
            gold_bias
    }


    nueva = pd.DataFrame(
        [nueva_lectura]
    )


    if os.path.exists(
        ARCHIVO_HISTORIAL
    ):

        anterior = pd.read_csv(
            ARCHIVO_HISTORIAL
        )

        historial = pd.concat(
            [anterior, nueva],
            ignore_index=True
        )

    else:

        historial = nueva


    historial.to_csv(
        ARCHIVO_HISTORIAL,
        index=False
    )


    print(
        "\nLecturas guardadas:",
        len(historial)
    )

    print(
        "Historial:",
        ARCHIVO_HISTORIAL
    )


    # ========================================================
    # ALERTA
    # ========================================================

    if usd >= 80:

        print("\n🚨 ALERTA")

        print(
            "USD EXTREMADAMENTE FUERTE"
        )

        print(
            "EURUSD -> buscar contexto BAJISTA"
        )

        print(
            "GBPUSD -> buscar contexto BAJISTA"
        )


    elif usd <= 20:

        print("\n🚨 ALERTA")

        print(
            "USD EXTREMADAMENTE DEBIL"
        )

        print(
            "EURUSD -> buscar contexto ALCISTA"
        )

        print(
            "GBPUSD -> buscar contexto ALCISTA"
        )


    else:

        print(
            "\nSin señal extrema USD."
        )


    print("\n" + "=" * 70)

    print(
        "LECTURA FINALIZADA ✓"
    )

    print("=" * 70)


# ============================================================
# 5. EJECUTAR UNA VEZ
# GitHub Actions será responsable de llamarlo cada hora.
# ============================================================

if __name__ == "__main__":

    ejecutar_market_regime()
