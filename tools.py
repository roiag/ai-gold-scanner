"""
כלים (Tools) לסוכן AI - שליפת נתונים וחישוב אינדיקטורים.

כל פונקציה כאן היא Tool ש-LLM יכול לקרוא לו בזמן ניתוח הגרף.
"""

import json
import yfinance as yf
import pandas as pd
import numpy as np
from langchain_core.tools import tool
from typing import Optional


# ─────────────────────────────────────────
#  DATA FETCHING
# ─────────────────────────────────────────

GOLD_SYMBOL = "GC=F"  # Gold Futures CME
GOLD_SYMBOL_BACKUP = "XAUUSD=X"

TIMEFRAME_CONFIG = {
    "1m":  {"interval": "1m",  "period": "1d"},
    "5m":  {"interval": "5m",  "period": "5d"},
    "15m": {"interval": "15m", "period": "5d"},
}


@tool
def get_gold_chart(timeframe: str) -> str:
    """
    שולף נתוני נרות של זהב (Gold Futures) עבור טיים-פריים מסוים.
    הטיים-פריים יכול להיות: "1m" (דקה), "5m" (5 דקות), או "15m" (15 דקות).
    מחזיר את 50 הנרות האחרונים עם: Open, High, Low, Close, Volume.
    """
    if timeframe not in TIMEFRAME_CONFIG:
        return f"שגיאה: טיים-פריים לא תקין '{timeframe}'. השתמש ב: 1m, 5m, 15m"

    cfg = TIMEFRAME_CONFIG[timeframe]

    try:
        ticker = yf.Ticker(GOLD_SYMBOL)
        df = ticker.history(interval=cfg["interval"], period=cfg["period"])

        if df.empty:
            ticker = yf.Ticker(GOLD_SYMBOL_BACKUP)
            df = ticker.history(interval=cfg["interval"], period=cfg["period"])

        if df.empty:
            return "שגיאה: לא התקבלו נתונים מהשרת."

        # ניקוי
        for col in ["Dividends", "Stock Splits"]:
            if col in df.columns:
                df.drop(columns=[col], inplace=True)

        # 50 נרות אחרונים
        df = df.tail(50)
        df.index = df.index.strftime("%Y-%m-%d %H:%M")

        return df.to_string()

    except Exception as e:
        return f"שגיאה בשליפת נתונים: {e}"


@tool
def get_current_gold_price() -> str:
    """מחזיר את מחיר הזהב הנוכחי (Close האחרון)."""
    try:
        ticker = yf.Ticker(GOLD_SYMBOL)
        data = ticker.history(period="1d", interval="1m")
        if data.empty:
            ticker = yf.Ticker(GOLD_SYMBOL_BACKUP)
            data = ticker.history(period="1d", interval="1m")
        if data.empty:
            return "שגיאה: לא ניתן לקבל מחיר נוכחי"
        price = float(data["Close"].iloc[-1])
        return f"מחיר זהב נוכחי: ${price:,.2f}"
    except Exception as e:
        return f"שגיאה: {e}"


# ─────────────────────────────────────────
#  TECHNICAL INDICATORS
# ─────────────────────────────────────────

def _fetch_df(timeframe: str, bars: int = 300) -> Optional[pd.DataFrame]:
    """פונקציית עזר פנימית - שליפת DataFrame גולמי."""
    cfg = TIMEFRAME_CONFIG.get(timeframe)
    if not cfg:
        return None
    try:
        ticker = yf.Ticker(GOLD_SYMBOL)
        df = ticker.history(interval=cfg["interval"], period=cfg["period"])
        if df.empty:
            ticker = yf.Ticker(GOLD_SYMBOL_BACKUP)
            df = ticker.history(interval=cfg["interval"], period=cfg["period"])
        if df.empty:
            return None
        for col in ["Dividends", "Stock Splits"]:
            if col in df.columns:
                df.drop(columns=[col], inplace=True)
        return df.tail(bars)
    except Exception:
        return None


@tool
def calculate_indicators(timeframe: str) -> str:
    """
    מחשב אינדיקטורים טכניים על גרף זהב עבור טיים-פריים מסוים.
    מחזיר: EMA 50, EMA 200, ATR(14), RSI(14), VWAP, וזיהוי Volume Spike.
    הטיים-פריים יכול להיות: "1m", "5m", "15m".
    """
    df = _fetch_df(timeframe, bars=300)
    if df is None or len(df) < 201:
        return f"שגיאה: אין מספיק נתונים לחישוב אינדיקטורים עבור {timeframe}."

    close = df["Close"]
    high = df["High"]
    low = df["Low"]

    # EMA
    ema50 = close.ewm(span=50, adjust=False).mean()
    ema200 = close.ewm(span=200, adjust=False).mean()

    # ATR
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = true_range.ewm(span=14, adjust=False).mean()

    # RSI
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)
    avg_gain = gain.ewm(span=14, adjust=False).mean()
    avg_loss = loss.ewm(span=14, adjust=False).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    # VWAP
    if df["Volume"].sum() > 0:
        typical = (high + low + close) / 3
        vwap = (typical * df["Volume"]).cumsum() / df["Volume"].cumsum()
    else:
        vwap = close

    # Volume spike
    avg_vol = df["Volume"].rolling(20).mean()
    vol_spike = df["Volume"].iloc[-1] > (avg_vol.iloc[-1] * 1.5) if pd.notna(avg_vol.iloc[-1]) else False

    # Last values
    last = df.iloc[-1]
    prev = df.iloc[-2]

    # Trend
    trend = "שורי (BULLISH)" if ema50.iloc[-1] > ema200.iloc[-1] else "דובי (BEARISH)"
    ema_gap = abs(ema50.iloc[-1] - ema200.iloc[-1])

    # Pullback detection
    pullback = ""
    if ema50.iloc[-1] > ema200.iloc[-1]:  # bullish
        if prev["Low"] <= ema50.iloc[-2] * 1.002 and last["Close"] > ema50.iloc[-1]:
            pullback = "✅ זוהתה נסיגה ל-EMA 50 עם חזרה שורית (Pullback Continuation)"
        elif prev["Low"] <= ema200.iloc[-2] * 1.005 and last["Close"] > ema50.iloc[-1]:
            pullback = "✅ זוהתה נסיגה עמוקה ל-EMA 200 עם התאוששות"
    else:  # bearish
        if prev["High"] >= ema50.iloc[-2] * 0.998 and last["Close"] < ema50.iloc[-1]:
            pullback = "✅ זוהתה נסיגה ל-EMA 50 עם חזרה דובית (Pullback Continuation)"
        elif prev["High"] >= ema200.iloc[-2] * 0.995 and last["Close"] < ema50.iloc[-1]:
            pullback = "✅ זוהתה נסיגה לאזור EMA 200 עם דחייה"

    # Candle analysis
    body = last["Close"] - last["Open"]
    candle_range = last["High"] - last["Low"]
    candle_type = ""
    if candle_range > 0:
        body_ratio = abs(body) / candle_range
        if body > 0 and body_ratio > 0.6:
            candle_type = "נר שורי חזק (גוף מלא)"
        elif body < 0 and body_ratio > 0.6:
            candle_type = "נר דובי חזק (גוף מלא)"
        elif abs(body) / candle_range < 0.2:
            candle_type = "דוג'י (חוסר החלטיות)"
        else:
            candle_type = "נר רגיל"

    result = {
        "טיים_פריים": timeframe,
        "מחיר_נוכחי": round(float(last["Close"]), 2),
        "EMA_50": round(float(ema50.iloc[-1]), 2),
        "EMA_200": round(float(ema200.iloc[-1]), 2),
        "מגמה": trend,
        "מרחק_בין_EMAs": round(float(ema_gap), 2),
        "ATR_14": round(float(atr.iloc[-1]), 2),
        "RSI_14": round(float(rsi.iloc[-1]), 1),
        "VWAP": round(float(vwap.iloc[-1]), 2),
        "מחיר_מעל_VWAP": bool(last["Close"] > vwap.iloc[-1]),
        "נפח_חריג": bool(vol_spike),
        "סוג_נר_אחרון": candle_type,
        "נסיגה_ל_EMA": pullback if pullback else "לא זוהתה נסיגה",
        "High_אחרון": round(float(last["High"]), 2),
        "Low_אחרון": round(float(last["Low"]), 2),
        "Open_אחרון": round(float(last["Open"]), 2),
    }

    return json.dumps(result, ensure_ascii=False, indent=2)


@tool
def calculate_trade_levels(entry_price: float, trade_type: str, atr_value: float, atr_multiplier: float = 1.5) -> str:
    """
    מחשב רמות סטופ-לוס ויעדי רווח לעסקה.
    entry_price: מחיר הכניסה
    trade_type: "LONG" או "SHORT"
    atr_value: ערך ה-ATR הנוכחי
    atr_multiplier: מכפיל ATR לסטופ-לוס (ברירת מחדל 1.5)
    """
    trade_type = trade_type.upper()
    if trade_type not in ("LONG", "SHORT"):
        return "שגיאה: trade_type חייב להיות LONG או SHORT"

    risk = atr_value * atr_multiplier

    if trade_type == "LONG":
        sl = entry_price - risk
        tp1 = entry_price + risk          # 1:1
        tp2 = entry_price + (risk * 2)    # 1:2
        tp3 = entry_price + (risk * 3)    # 1:3
    else:
        sl = entry_price + risk
        tp1 = entry_price - risk
        tp2 = entry_price - (risk * 2)
        tp3 = entry_price - (risk * 3)

    result = {
        "סוג_עסקה": trade_type,
        "מחיר_כניסה": round(entry_price, 2),
        "סטופ_לוס": round(sl, 2),
        "יעד_1_RR_1_1": round(tp1, 2),
        "יעד_2_RR_1_2": round(tp2, 2),
        "יעד_3_RR_1_3": round(tp3, 2),
        "סיכון_בנקודות": round(risk, 2),
        "רווח_ביעד_2": round(risk * 2, 2),
        "יחס_סיכוי_סיכון": "1:2",
    }

    return json.dumps(result, ensure_ascii=False, indent=2)


# רשימת כל הכלים לייצוא
ALL_TOOLS = [
    get_gold_chart,
    get_current_gold_price,
    calculate_indicators,
    calculate_trade_levels,
]
