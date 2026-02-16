"""
מודול התראות - שליחת Windows Toast Notifications + צליל כשהסוכן מזהה הזדמנות.
"""

import winsound
import re
from winotify import Notification, audio


APP_ID = "AI Gold Scanner"
ICON_PATH = ""  # אפשר להוסיף נתיב לאייקון


def send_alert(title: str, message: str, sound: bool = True):
    """
    שולח התראת Windows Toast Notification.

    Args:
        title: כותרת ההתראה
        message: תוכן ההתראה
        sound: האם להשמיע צליל
    """
    try:
        toast = Notification(
            app_id=APP_ID,
            title=title,
            msg=message[:250],  # Windows מגביל אורך הודעה
            duration="long",
        )
        toast.set_audio(audio.Default, loop=False)
        toast.show()
    except Exception as e:
        print(f"⚠️ שגיאה בשליחת התראה: {e}")

    # צליל נוסף לתשומת לב
    if sound:
        try:
            winsound.Beep(1000, 300)  # 1000Hz, 300ms
            winsound.Beep(1500, 300)
            winsound.Beep(2000, 300)
        except Exception:
            pass


def parse_and_alert(agent_response: str, timeframe: str):
    """
    מנתח את תשובת הסוכן ושולח התראה אם זוהתה הזדמנות.

    Args:
        agent_response: הטקסט המלא שהסוכן החזיר
        timeframe: הטיים-פריים שנסרק

    Returns:
        True אם נשלחה התראה, False אם לא
    """
    text = agent_response.upper()

    # זיהוי אם יש עסקה
    has_long = any(kw in text for kw in ["LONG", "לונג", "קנייה", "BUY", "BULLISH ENTRY"])
    has_short = any(kw in text for kw in ["SHORT", "שורט", "מכירה", "SELL", "BEARISH ENTRY"])
    has_entry = any(kw in text for kw in ["ENTRY PRICE", "מחיר כניסה", "ENTRY:", "כניסה:"])
    has_no_opportunity = any(kw in text for kw in [
        "NO OPPORTUNITY", "NO TRADE", "אין הזדמנות", "לא נמצאה",
        "NO CLEAR", "NOT RECOMMENDED", "WAIT", "NO SIGNAL"
    ])

    if has_no_opportunity and not has_entry:
        return False

    if not (has_long or has_short) or not has_entry:
        return False

    # חילוץ פרטי העסקה
    trade_type = "🟢 LONG (קנייה)" if has_long else "🔴 SHORT (מכירה)"

    # חילוץ מחירים מהטקסט
    entry = _extract_price(agent_response, r"(?:entry\s*(?:price)?|כניסה)[:\s]*\$?([\d,]+\.?\d*)")
    sl = _extract_price(agent_response, r"(?:stop[ -]?loss|סטופ)[:\s]*\$?([\d,]+\.?\d*)")
    tp = _extract_price(agent_response, r"(?:TP2|tp2|יעד\s*2|target\s*2)[:\s]*\$?([\d,]+\.?\d*)")

    tf_labels = {"1m": "דקה", "5m": "5 דקות", "15m": "15 דקות"}
    tf_label = tf_labels.get(timeframe, timeframe)

    # בניית הודעה
    title = f"🔔 {trade_type} | גרף {tf_label}"

    lines = []
    if entry:
        lines.append(f"💰 כניסה: ${entry}")
    if sl:
        lines.append(f"🛑 SL: ${sl}")
    if tp:
        lines.append(f"🎯 יעד: ${tp}")

    message = "\n".join(lines) if lines else "הזדמנות מסחר זוהתה! בדוק את המסך."

    send_alert(title, message, sound=True)
    return True


def _extract_price(text: str, pattern: str) -> str:
    """חילוץ מחיר מטקסט באמצעות regex."""
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        price = match.group(1).replace(",", "")
        try:
            return f"{float(price):,.2f}"
        except ValueError:
            return ""
    return ""


def send_scan_start_notification():
    """התראה שהסריקה התחילה."""
    try:
        toast = Notification(
            app_id=APP_ID,
            title="🏆 AI Gold Scanner פעיל",
            msg="הסוכן סורק גרפים כל 5 דקות. התראות ישלחו בזיהוי הזדמנות.",
            duration="short",
        )
        toast.show()
    except Exception:
        pass


def send_scan_summary(total_signals: int, scan_count: int):
    """התראת סיכום."""
    try:
        toast = Notification(
            app_id=APP_ID,
            title="📊 סיכום סריקה",
            msg=f"בוצעו {scan_count} סריקות. נמצאו {total_signals} הזדמנויות.",
            duration="short",
        )
        toast.show()
    except Exception:
        pass
