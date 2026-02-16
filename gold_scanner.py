"""
AI Gold Scanner - סוכן מסחר יומי בזהב
========================================

סוכן AI המתמחה במסחר יומי בזהב (XAUUSD).
סורק גרפים בטיים-פריימים של 1 דקה, 5 דקות ו-15 דקות
ומחפש הזדמנויות מסחר בהתבסס על אסטרטגיית AI Gold Institutional Scalper.

שימוש:
    python gold_scanner.py              # סריקה חד-פעמית
    python gold_scanner.py --loop       # סריקה מתמשכת
    python gold_scanner.py --interval 60  # סריקה כל 60 שניות
"""

import argparse
import time
import sys
from datetime import datetime
from typing import List

from data_fetcher import fetch_gold_data, get_current_price, TIMEFRAME_MAP
from strategy import GoldStrategy, TradeSignal
from display import (
    print_header, print_scanning_status, print_no_signal,
    print_signal, print_summary, print_error, print_info,
    clear_screen, Colors, enable_windows_ansi
)


TIMEFRAMES = ["1m", "5m", "15m"]


def run_scan(strategy: GoldStrategy, timeframes: List[str] = None) -> List[TradeSignal]:
    """
    הרצת סריקה אחת על כל הטיים-פריימים.

    Returns:
        רשימת אותות שזוהו
    """
    timeframes = timeframes or TIMEFRAMES
    signals = []

    # קבלת מחיר נוכחי
    try:
        current_price = get_current_price()
    except Exception:
        current_price = None

    for tf in timeframes:
        print_scanning_status(tf, current_price)

        try:
            df = fetch_gold_data(tf, bars=300)

            if df is None or len(df) < 210:
                print(f"{Colors.DIM}   ↳ אין מספיק נתונים לגרף {tf} ({len(df) if df is not None else 0} נרות){Colors.RESET}")
                continue

            signal = strategy.analyze(df, tf)

            if signal:
                signals.append(signal)
                print_signal(signal)
            else:
                print_no_signal(tf)

        except Exception as e:
            print_error(f"שגיאה בסריקת גרף {tf}: {e}")

    return signals


def main():
    """נקודת כניסה ראשית."""
    enable_windows_ansi()

    parser = argparse.ArgumentParser(
        description="AI Gold Scanner - סוכן מסחר יומי בזהב",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
דוגמאות שימוש:
  python gold_scanner.py                    # סריקה חד-פעמית
  python gold_scanner.py --loop             # סריקה מתמשכת (כל 30 שניות)
  python gold_scanner.py --loop --interval 60  # סריקה כל דקה
  python gold_scanner.py --timeframes 5m 15m   # רק גרפים של 5 ו-15 דקות
  python gold_scanner.py --confidence 60    # סף ביטחון מינימלי 60%
  python gold_scanner.py --rr 3             # יחס סיכוי-סיכון 1:3
        """
    )

    parser.add_argument(
        "--loop", action="store_true",
        help="הפעלת סריקה מתמשכת (ברירת מחדל: סריקה חד-פעמית)"
    )
    parser.add_argument(
        "--interval", type=int, default=30,
        help="מרווח בשניות בין סריקות (ברירת מחדל: 30)"
    )
    parser.add_argument(
        "--timeframes", nargs="+", choices=["1m", "5m", "15m"],
        default=["1m", "5m", "15m"],
        help="טיים-פריימים לסריקה (ברירת מחדל: 1m 5m 15m)"
    )
    parser.add_argument(
        "--ema-fast", type=int, default=50,
        help="תקופת EMA מהיר (ברירת מחדל: 50)"
    )
    parser.add_argument(
        "--ema-slow", type=int, default=200,
        help="תקופת EMA איטי (ברירת מחדל: 200)"
    )
    parser.add_argument(
        "--atr-period", type=int, default=14,
        help="תקופת ATR (ברירת מחדל: 14)"
    )
    parser.add_argument(
        "--atr-multiplier", type=float, default=1.5,
        help="מכפיל ATR לסטופ-לוס (ברירת מחדל: 1.5)"
    )
    parser.add_argument(
        "--rr", type=float, default=2.0,
        help="יחס סיכוי-סיכון (ברירת מחדל: 2.0)"
    )
    parser.add_argument(
        "--confidence", type=float, default=50,
        help="סף ביטחון מינימלי באחוזים (ברירת מחדל: 50)"
    )

    args = parser.parse_args()

    # יצירת אסטרטגיה עם הפרמטרים
    strategy = GoldStrategy(
        ema_fast=args.ema_fast,
        ema_slow=args.ema_slow,
        atr_period=args.atr_period,
        atr_sl_multiplier=args.atr_multiplier,
        risk_reward=args.rr,
        min_confidence=args.confidence,
    )

    # הצגת כותרת
    clear_screen()
    print_header()

    print_info(f"הגדרות: EMA {args.ema_fast}/{args.ema_slow} | ATR {args.atr_period} (x{args.atr_multiplier}) | R:R 1:{args.rr} | ביטחון מינימלי: {args.confidence}%")
    print_info(f"טיים-פריימים: {', '.join(args.timeframes)}")

    if args.loop:
        print_info(f"מצב: סריקה מתמשכת כל {args.interval} שניות")
        print_info("לחץ Ctrl+C לעצירה\n")
    else:
        print_info("מצב: סריקה חד-פעמית\n")

    scan_count = 0
    total_signals = []

    try:
        while True:
            scan_count += 1
            now = datetime.now().strftime("%H:%M:%S")
            print(f"\n{Colors.BOLD}{Colors.BLUE}{'─' * 62}")
            print(f"🔍 סריקה #{scan_count} | {now}")
            print(f"{'─' * 62}{Colors.RESET}")

            signals = run_scan(strategy, args.timeframes)
            total_signals.extend(signals)

            if signals:
                print_summary(signals)
            else:
                print(f"\n{Colors.DIM}   אין הזדמנויות בסריקה הנוכחית. ממשיך לחפש...{Colors.RESET}")

            if not args.loop:
                break

            # המתנה לסריקה הבאה עם ספירה לאחור
            print(f"\n{Colors.DIM}⏳ סריקה הבאה בעוד {args.interval} שניות...{Colors.RESET}", end="", flush=True)
            try:
                time.sleep(args.interval)
                print()  # שורה חדשה אחרי ההמתנה
            except KeyboardInterrupt:
                raise

    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}⏹️  הסריקה הופסקה על ידי המשתמש.{Colors.RESET}")
        if total_signals:
            print(f"\n{Colors.BOLD}סה\"כ {len(total_signals)} אותות זוהו ב-{scan_count} סריקות:{Colors.RESET}")
            print_summary(total_signals)
        print(f"\n{Colors.GREEN}👋 להתראות! סחרו בחכמה.{Colors.RESET}\n")
        sys.exit(0)

    # סיום סריקה חד-פעמית
    if not args.loop:
        if total_signals:
            print(f"\n{Colors.BOLD}✅ סריקה הושלמה. נמצאו {len(total_signals)} הזדמנויות.{Colors.RESET}")
        else:
            print(f"\n{Colors.YELLOW}📭 סריקה הושלמה. לא נמצאו הזדמנויות כרגע.")
            print(f"    💡 טיפ: הרץ עם --loop לסריקה מתמשכת{Colors.RESET}")


if __name__ == "__main__":
    main()
