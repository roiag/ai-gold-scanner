"""
מודול לשליפת נתוני זהב בזמן אמת ממספר מקורות.
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional


# סימבולים אפשריים לזהב
GOLD_SYMBOLS = {
    "yfinance": "GC=F",       # Gold Futures (CME)
    "xauusd": "XAUUSD=X",     # Gold Spot USD
}

TIMEFRAME_MAP = {
    "1m":  {"interval": "1m",  "period": "1d",  "label": "דקה אחת"},
    "5m":  {"interval": "5m",  "period": "5d",  "label": "5 דקות"},
    "15m": {"interval": "15m", "period": "5d",  "label": "15 דקות"},
}


def fetch_gold_data(timeframe: str = "1m", bars: int = 300, symbol: Optional[str] = None) -> pd.DataFrame:
    """
    שליפת נתוני נרות זהב לפי טיים-פריים.

    Args:
        timeframe: "1m", "5m", או "15m"
        bars: מספר נרות מקסימלי לשליפה
        symbol: סימבול מותאם אישית (אופציונלי)

    Returns:
        DataFrame עם עמודות: Open, High, Low, Close, Volume
    """
    if timeframe not in TIMEFRAME_MAP:
        raise ValueError(f"טיים-פריים לא תקין: {timeframe}. אפשרויות: {list(TIMEFRAME_MAP.keys())}")

    tf_config = TIMEFRAME_MAP[timeframe]
    ticker_symbol = symbol or GOLD_SYMBOLS["yfinance"]

    try:
        ticker = yf.Ticker(ticker_symbol)
        df = ticker.history(
            interval=tf_config["interval"],
            period=tf_config["period"],
        )

        if df.empty:
            # נסיון עם סימבול חלופי
            ticker_symbol = GOLD_SYMBOLS["xauusd"]
            ticker = yf.Ticker(ticker_symbol)
            df = ticker.history(
                interval=tf_config["interval"],
                period=tf_config["period"],
            )

        if df.empty:
            raise RuntimeError(f"לא התקבלו נתונים עבור {ticker_symbol}")

        # ניקוי עמודות מיותרות
        if "Dividends" in df.columns:
            df.drop(columns=["Dividends"], inplace=True)
        if "Stock Splits" in df.columns:
            df.drop(columns=["Stock Splits"], inplace=True)

        # חיתוך למספר הנרות המבוקש
        if len(df) > bars:
            df = df.tail(bars)

        return df

    except Exception as e:
        raise RuntimeError(f"שגיאה בשליפת נתוני זהב ({ticker_symbol}, {timeframe}): {e}")


def get_current_price() -> float:
    """מחזיר את מחיר הזהב העדכני ביותר."""
    try:
        ticker = yf.Ticker(GOLD_SYMBOLS["yfinance"])
        data = ticker.history(period="1d", interval="1m")
        if data.empty:
            ticker = yf.Ticker(GOLD_SYMBOLS["xauusd"])
            data = ticker.history(period="1d", interval="1m")
        if data.empty:
            raise RuntimeError("לא ניתן לקבל מחיר נוכחי")
        return float(data["Close"].iloc[-1])
    except Exception as e:
        raise RuntimeError(f"שגיאה בקבלת מחיר נוכחי: {e}")


if __name__ == "__main__":
    # בדיקה מהירה
    for tf in ["1m", "5m", "15m"]:
        try:
            df = fetch_gold_data(tf, bars=50)
            print(f"\n[{TIMEFRAME_MAP[tf]['label']}] נשלפו {len(df)} נרות")
            print(df.tail(3))
        except Exception as e:
            print(f"שגיאה ב-{tf}: {e}")
