"""
מודול אינדיקטורים טכניים - מבוסס על האסטרטגיה של AI Gold Institutional Scalper.

אינדיקטורים:
- EMA 50 / EMA 200 (מגמה מוסדית)
- ATR 14 (תנודתיות דינמית)
- RSI 14 (מומנטום)
- VWAP (נפח מוסדי)
- Liquidity Levels (זיהוי שבירות נזילות)
"""

import pandas as pd
import numpy as np
from typing import Tuple


def calc_ema(series: pd.Series, period: int) -> pd.Series:
    """חישוב Exponential Moving Average."""
    return series.ewm(span=period, adjust=False).mean()


def calc_sma(series: pd.Series, period: int) -> pd.Series:
    """חישוב Simple Moving Average."""
    return series.rolling(window=period).mean()


def calc_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    חישוב Average True Range.
    ATR משמש לקביעת סטופ-לוס דינמי.
    """
    high = df["High"]
    low = df["Low"]
    close = df["Close"]

    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()

    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = true_range.ewm(span=period, adjust=False).mean()
    return atr


def calc_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """חישוב Relative Strength Index."""
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)

    avg_gain = gain.ewm(span=period, adjust=False).mean()
    avg_loss = loss.ewm(span=period, adjust=False).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calc_vwap(df: pd.DataFrame) -> pd.Series:
    """חישוב Volume Weighted Average Price."""
    typical_price = (df["High"] + df["Low"] + df["Close"]) / 3
    cumulative_tp_vol = (typical_price * df["Volume"]).cumsum()
    cumulative_vol = df["Volume"].cumsum()
    vwap = cumulative_tp_vol / cumulative_vol
    return vwap


def calc_bollinger_bands(series: pd.Series, period: int = 20, std_dev: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """חישוב Bollinger Bands."""
    sma = calc_sma(series, period)
    std = series.rolling(window=period).std()
    upper = sma + (std_dev * std)
    lower = sma - (std_dev * std)
    return upper, sma, lower


def detect_liquidity_levels(df: pd.DataFrame, lookback: int = 20) -> Tuple[pd.Series, pd.Series]:
    """
    זיהוי רמות נזילות - שיאים ושפלים מקומיים שמשמשים כאזורי נזילות מוסדית.
    שבירה של רמות אלה מעידה על כניסת שחקנים מוסדיים.
    """
    swing_highs = pd.Series(np.nan, index=df.index)
    swing_lows = pd.Series(np.nan, index=df.index)

    for i in range(lookback, len(df) - lookback):
        window_high = df["High"].iloc[i - lookback:i + lookback + 1]
        window_low = df["Low"].iloc[i - lookback:i + lookback + 1]

        if df["High"].iloc[i] == window_high.max():
            swing_highs.iloc[i] = df["High"].iloc[i]

        if df["Low"].iloc[i] == window_low.min():
            swing_lows.iloc[i] = df["Low"].iloc[i]

    # מילוי הרמות האחרונות קדימה
    swing_highs = swing_highs.ffill()
    swing_lows = swing_lows.ffill()

    return swing_highs, swing_lows


def detect_volume_spike(df: pd.DataFrame, multiplier: float = 1.5, period: int = 20) -> pd.Series:
    """
    זיהוי נפח חריג (Volume Spike).
    נפח חריג מעיד על פעילות מוסדית ומחזק את אותות המסחר.
    """
    avg_volume = df["Volume"].rolling(window=period).mean()
    return df["Volume"] > (avg_volume * multiplier)


def calc_momentum(series: pd.Series, period: int = 10) -> pd.Series:
    """חישוב מומנטום פשוט."""
    return series - series.shift(period)


def add_all_indicators(df: pd.DataFrame, ema_fast: int = 50, ema_slow: int = 200,
                        atr_period: int = 14, rsi_period: int = 14) -> pd.DataFrame:
    """
    הוספת כל האינדיקטורים ל-DataFrame.

    Args:
        df: DataFrame עם עמודות OHLCV
        ema_fast: תקופת EMA מהיר (ברירת מחדל: 50)
        ema_slow: תקופת EMA איטי (ברירת מחדל: 200)
        atr_period: תקופת ATR (ברירת מחדל: 14)
        rsi_period: תקופת RSI (ברירת מחדל: 14)

    Returns:
        DataFrame עם כל האינדיקטורים
    """
    df = df.copy()

    # EMAs - מגמה מוסדית
    df["EMA_fast"] = calc_ema(df["Close"], ema_fast)
    df["EMA_slow"] = calc_ema(df["Close"], ema_slow)

    # ATR - תנודתיות דינמית
    df["ATR"] = calc_atr(df, atr_period)

    # RSI - מומנטום
    df["RSI"] = calc_rsi(df["Close"], rsi_period)

    # VWAP - נפח מוסדי
    if df["Volume"].sum() > 0:
        df["VWAP"] = calc_vwap(df)
    else:
        df["VWAP"] = df["Close"]  # fallback אם אין נתוני נפח

    # Bollinger Bands
    df["BB_upper"], df["BB_mid"], df["BB_lower"] = calc_bollinger_bands(df["Close"])

    # Volume Spike
    df["volume_spike"] = detect_volume_spike(df)

    # רמות נזילות
    df["liquidity_high"], df["liquidity_low"] = detect_liquidity_levels(df, lookback=10)

    # מומנטום
    df["momentum"] = calc_momentum(df["Close"], period=10)

    # כיוון מגמה: True = שורי, False = דובי
    df["trend_bullish"] = df["EMA_fast"] > df["EMA_slow"]

    return df
