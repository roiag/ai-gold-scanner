"""
מנוע האסטרטגיה - AI Gold Institutional Scalper.

מבוסס על:
- מבנה EMA מוסדי (50/200) לזיהוי מגמה דומיננטית
- ATR לסטופ-לוס דינמי
- יחס סיכוי-סיכון קבוע (1:2 ברירת מחדל)
- אישור נפח (Volume Confirmation)
- זיהוי שבירת נזילות (Liquidity Break Detection)
- כניסה בהמשך מגמה לאחר נסיגה (Pullback Continuation)
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
from indicators import add_all_indicators


@dataclass
class TradeSignal:
    """ייצוג אות מסחר."""
    signal_type: str           # "LONG" או "SHORT"
    entry_price: float         # מחיר כניסה
    stop_loss: float           # סטופ-לוס
    take_profit_1: float       # יעד רווח 1 (1:1)
    take_profit_2: float       # יעד רווח 2 (1:2)
    take_profit_3: float       # יעד רווח 3 (1:3)
    timeframe: str             # טיים-פריים
    timestamp: datetime        # זמן האות
    confidence: float          # רמת ביטחון (0-100)
    description_he: str        # תיאור בעברית
    indicators: dict = field(default_factory=dict)  # ערכי אינדיקטורים

    @property
    def risk_points(self) -> float:
        return abs(self.entry_price - self.stop_loss)

    @property
    def reward_points(self) -> float:
        return abs(self.take_profit_2 - self.entry_price)

    @property
    def risk_reward_ratio(self) -> float:
        if self.risk_points == 0:
            return 0
        return self.reward_points / self.risk_points


class GoldStrategy:
    """
    אסטרטגיית מסחר מוסדית בזהב.
    """

    def __init__(
        self,
        ema_fast: int = 50,
        ema_slow: int = 200,
        atr_period: int = 14,
        atr_sl_multiplier: float = 1.5,
        risk_reward: float = 2.0,
        rsi_period: int = 14,
        rsi_overbought: float = 70,
        rsi_oversold: float = 30,
        min_confidence: float = 50,
    ):
        self.ema_fast = ema_fast
        self.ema_slow = ema_slow
        self.atr_period = atr_period
        self.atr_sl_multiplier = atr_sl_multiplier
        self.risk_reward = risk_reward
        self.rsi_period = rsi_period
        self.rsi_overbought = rsi_overbought
        self.rsi_oversold = rsi_oversold
        self.min_confidence = min_confidence

    def analyze(self, df: pd.DataFrame, timeframe: str) -> Optional[TradeSignal]:
        """
        ניתוח גרף וחיפוש הזדמנות מסחר.

        Args:
            df: DataFrame עם נתוני OHLCV
            timeframe: "1m", "5m", או "15m"

        Returns:
            TradeSignal אם יש הזדמנות, None אחרת
        """
        if len(df) < self.ema_slow + 10:
            return None

        # הוספת אינדיקטורים
        df = add_all_indicators(
            df,
            ema_fast=self.ema_fast,
            ema_slow=self.ema_slow,
            atr_period=self.atr_period,
            rsi_period=self.rsi_period,
        )

        # בדיקת LONG
        long_signal = self._check_long(df, timeframe)
        if long_signal:
            return long_signal

        # בדיקת SHORT
        short_signal = self._check_short(df, timeframe)
        if short_signal:
            return short_signal

        return None

    def _check_long(self, df: pd.DataFrame, timeframe: str) -> Optional[TradeSignal]:
        """בדיקת תנאים לעסקת LONG."""
        last = df.iloc[-1]
        prev = df.iloc[-2]
        prev2 = df.iloc[-3]

        confidence = 0
        reasons = []

        # ===== תנאי 1: מגמה שורית - EMA 50 מעל EMA 200 =====
        if last["EMA_fast"] > last["EMA_slow"]:
            confidence += 25
            reasons.append("מגמה שורית: EMA 50 מעל EMA 200")
        else:
            return None  # תנאי חובה

        # ===== תנאי 2: נסיגה ל-EMA והמשך מגמה (Pullback Continuation) =====
        pullback_to_ema = (
            prev["Low"] <= prev["EMA_fast"] * 1.002 and  # נסיגה לאזור ה-EMA
            last["Close"] > last["EMA_fast"]              # חזרה מעל ה-EMA
        )
        if pullback_to_ema:
            confidence += 20
            reasons.append("נסיגה ל-EMA 50 עם חזרה שורית")

        # נסיגה עמוקה יותר ל-EMA 200
        deep_pullback = (
            prev["Low"] <= prev["EMA_slow"] * 1.005 and
            last["Close"] > last["EMA_fast"]
        )
        if deep_pullback:
            confidence += 10
            reasons.append("נסיגה עמוקה ל-EMA 200 עם התאוששות")

        # ===== תנאי 3: RSI - מומנטום חיובי =====
        if 40 < last["RSI"] < self.rsi_overbought:
            confidence += 10
            reasons.append(f"RSI באזור בריא: {last['RSI']:.1f}")
        elif last["RSI"] <= 40 and prev["RSI"] < last["RSI"]:
            confidence += 15
            reasons.append(f"RSI מתאושש מאזור מכירת יתר: {last['RSI']:.1f}")

        # ===== תנאי 4: אישור נפח =====
        if last["volume_spike"]:
            confidence += 10
            reasons.append("נפח מסחר חריג - פעילות מוסדית")

        # ===== תנאי 5: מחיר מעל VWAP =====
        if last["Close"] > last["VWAP"]:
            confidence += 5
            reasons.append("מחיר מעל VWAP - לחץ קניה מוסדי")

        # ===== תנאי 6: שבירת רמת נזילות =====
        if pd.notna(last["liquidity_high"]) and last["Close"] > last["liquidity_high"]:
            confidence += 10
            reasons.append("שבירת רמת נזילות עליונה")

        # ===== תנאי 7: נר שורי חזק =====
        body = last["Close"] - last["Open"]
        candle_range = last["High"] - last["Low"]
        if candle_range > 0 and body / candle_range > 0.6 and body > 0:
            confidence += 5
            reasons.append("נר שורי חזק עם גוף מלא")

        # ===== תנאי 8: מומנטום חיובי =====
        if last["momentum"] > 0 and prev["momentum"] <= 0:
            confidence += 5
            reasons.append("שינוי מומנטום לחיובי")

        if confidence < self.min_confidence:
            return None

        # חישוב רמות מסחר
        atr = last["ATR"]
        entry = last["Close"]
        stop_loss = entry - (atr * self.atr_sl_multiplier)
        risk = entry - stop_loss
        tp1 = entry + risk          # 1:1
        tp2 = entry + (risk * 2)    # 1:2
        tp3 = entry + (risk * 3)    # 1:3

        description = self._build_description("לונג", reasons, timeframe, entry, stop_loss, tp2)

        return TradeSignal(
            signal_type="LONG",
            entry_price=round(entry, 2),
            stop_loss=round(stop_loss, 2),
            take_profit_1=round(tp1, 2),
            take_profit_2=round(tp2, 2),
            take_profit_3=round(tp3, 2),
            timeframe=timeframe,
            timestamp=df.index[-1],
            confidence=min(confidence, 100),
            description_he=description,
            indicators={
                "EMA_fast": round(last["EMA_fast"], 2),
                "EMA_slow": round(last["EMA_slow"], 2),
                "ATR": round(atr, 2),
                "RSI": round(last["RSI"], 1),
                "VWAP": round(last["VWAP"], 2),
            }
        )

    def _check_short(self, df: pd.DataFrame, timeframe: str) -> Optional[TradeSignal]:
        """בדיקת תנאים לעסקת SHORT."""
        last = df.iloc[-1]
        prev = df.iloc[-2]
        prev2 = df.iloc[-3]

        confidence = 0
        reasons = []

        # ===== תנאי 1: מגמה דובית - EMA 50 מתחת ל-EMA 200 =====
        if last["EMA_fast"] < last["EMA_slow"]:
            confidence += 25
            reasons.append("מגמה דובית: EMA 50 מתחת ל-EMA 200")
        else:
            return None  # תנאי חובה

        # ===== תנאי 2: נסיגה ל-EMA והמשך מגמה (Pullback Continuation) =====
        pullback_to_ema = (
            prev["High"] >= prev["EMA_fast"] * 0.998 and  # נסיגה לאזור ה-EMA
            last["Close"] < last["EMA_fast"]                # חזרה מתחת ל-EMA
        )
        if pullback_to_ema:
            confidence += 20
            reasons.append("נסיגה ל-EMA 50 עם חזרה דובית")

        # נסיגה עמוקה יותר ל-EMA 200
        deep_pullback = (
            prev["High"] >= prev["EMA_slow"] * 0.995 and
            last["Close"] < last["EMA_fast"]
        )
        if deep_pullback:
            confidence += 10
            reasons.append("נסיגה לאזור EMA 200 עם דחייה")

        # ===== תנאי 3: RSI - מומנטום שלילי =====
        if self.rsi_oversold < last["RSI"] < 60:
            confidence += 10
            reasons.append(f"RSI באזור בריא לשורט: {last['RSI']:.1f}")
        elif last["RSI"] >= 60 and prev["RSI"] > last["RSI"]:
            confidence += 15
            reasons.append(f"RSI יורד מאזור קניית יתר: {last['RSI']:.1f}")

        # ===== תנאי 4: אישור נפח =====
        if last["volume_spike"]:
            confidence += 10
            reasons.append("נפח מסחר חריג - לחץ מכירה מוסדי")

        # ===== תנאי 5: מחיר מתחת ל-VWAP =====
        if last["Close"] < last["VWAP"]:
            confidence += 5
            reasons.append("מחיר מתחת ל-VWAP - לחץ מכירה")

        # ===== תנאי 6: שבירת רמת נזילות =====
        if pd.notna(last["liquidity_low"]) and last["Close"] < last["liquidity_low"]:
            confidence += 10
            reasons.append("שבירת רמת נזילות תחתונה")

        # ===== תנאי 7: נר דובי חזק =====
        body = last["Open"] - last["Close"]
        candle_range = last["High"] - last["Low"]
        if candle_range > 0 and body / candle_range > 0.6 and body > 0:
            confidence += 5
            reasons.append("נר דובי חזק עם גוף מלא")

        # ===== תנאי 8: מומנטום שלילי =====
        if last["momentum"] < 0 and prev["momentum"] >= 0:
            confidence += 5
            reasons.append("שינוי מומנטום לשלילי")

        if confidence < self.min_confidence:
            return None

        # חישוב רמות מסחר
        atr = last["ATR"]
        entry = last["Close"]
        stop_loss = entry + (atr * self.atr_sl_multiplier)
        risk = stop_loss - entry
        tp1 = entry - risk          # 1:1
        tp2 = entry - (risk * 2)    # 1:2
        tp3 = entry - (risk * 3)    # 1:3

        description = self._build_description("שורט", reasons, timeframe, entry, stop_loss, tp2)

        return TradeSignal(
            signal_type="SHORT",
            entry_price=round(entry, 2),
            stop_loss=round(stop_loss, 2),
            take_profit_1=round(tp1, 2),
            take_profit_2=round(tp2, 2),
            take_profit_3=round(tp3, 2),
            timeframe=timeframe,
            timestamp=df.index[-1],
            confidence=min(confidence, 100),
            description_he=description,
            indicators={
                "EMA_fast": round(last["EMA_fast"], 2),
                "EMA_slow": round(last["EMA_slow"], 2),
                "ATR": round(atr, 2),
                "RSI": round(last["RSI"], 1),
                "VWAP": round(last["VWAP"], 2),
            }
        )

    def _build_description(self, trade_type: str, reasons: List[str],
                           timeframe: str, entry: float, sl: float, tp: float) -> str:
        """בניית תיאור עסקה בעברית."""

        tf_labels = {"1m": "דקה", "5m": "5 דקות", "15m": "15 דקות"}
        tf_label = tf_labels.get(timeframe, timeframe)

        header = f"🔔 אות {trade_type} בגרף {tf_label}"
        risk = abs(entry - sl)
        reward = abs(tp - entry)

        lines = [
            header,
            "",
            "📊 ניתוח:",
        ]
        for i, reason in enumerate(reasons, 1):
            lines.append(f"  {i}. {reason}")

        lines.extend([
            "",
            f"💰 כניסה: ${entry:,.2f}",
            f"🛑 סטופ-לוס: ${sl:,.2f} (סיכון: ${risk:,.2f})",
            f"🎯 יעד: ${tp:,.2f} (רווח: ${reward:,.2f})",
            f"📐 יחס סיכוי/סיכון: 1:{reward/risk:.1f}" if risk > 0 else "",
        ])

        return "\n".join(lines)
