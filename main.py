"""
AI Gold Scanner - נקודת כניסה ראשית.

סוכן AI (LangGraph + Ollama) המתמחה במסחר יומי בזהב.
סורק גרפי 1m/5m/15m כל 5 דקות, ושולח התראות Windows כשמזהה הזדמנות.

שימוש:
    python main.py                          # סריקה מתמשכת כל 5 דקות + התראות
    python main.py --once                   # סריקה חד-פעמית
    python main.py --interval 120           # סריקה כל 2 דקות
    python main.py --ask "מה המצב בגרף של 5 דקות?"  # שאלה חופשית
"""

import argparse
import sys
import os
import time
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()


# ─────────────────────────────────────────
#  DISPLAY HELPERS
# ─────────────────────────────────────────

class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    DIM = "\033[2m"


def enable_terminal_colors():
    if sys.platform == "win32":
        os.system("")
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except Exception:
            pass


def print_banner():
    enable_terminal_colors()
    print(f"""{Colors.BOLD}{Colors.YELLOW}
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     🏆  AI Gold Agent - סוכן מסחר יומי בזהב  🏆            ║
║                                                              ║
║     🤖 LangGraph + Ollama (local LLM)                       ║
║     📊 סריקה: 1 דקה | 5 דקות | 15 דקות                     ║
║     🎯 אסטרטגיה: AI Gold Institutional Scalper              ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
{Colors.RESET}""")


def print_separator():
    now = datetime.now().strftime("%H:%M:%S")
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'─' * 62}")
    print(f"🔍 סריקה | {now}")
    print(f"{'─' * 62}{Colors.RESET}\n")


def print_thinking():
    print(f"{Colors.DIM}🤖 הסוכן חושב... (שולף נתונים, מחשב אינדיקטורים, מנתח...){Colors.RESET}\n")


def print_result(text: str):
    print(f"\n{Colors.CYAN}{'═' * 62}")
    print(f"📋 תוצאת הניתוח:")
    print(f"{'═' * 62}{Colors.RESET}\n")
    print(text)
    print(f"\n{Colors.DIM}{'═' * 62}{Colors.RESET}")


# ─────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────

TIMEFRAMES = ["1m", "5m", "15m"]
TF_LABELS = {"1m": "דקה", "5m": "5 דקות", "15m": "15 דקות"}


def scan_single_timeframe(agent, run_agent_fn, timeframe: str) -> tuple:
    """
    סורק טיים-פריים בודד ומחזיר את תשובת הסוכן.

    Returns:
        (response_text, had_opportunity)
    """
    tf_label = TF_LABELS.get(timeframe, timeframe)
    prompt = (
        f"נתח את גרף הזהב בטיים-פריים של {tf_label} ({timeframe}). "
        f"חשב אינדיקטורים (calculate_indicators) עבור {timeframe}. "
        f"אם יש הזדמנות, חשב רמות מסחר (calculate_trade_levels) והצג בפורמט המבוקש. "
        f"אם אין הזדמנות, אמור שאין הזדמנות ולמה."
    )
    response = run_agent_fn(agent, prompt)
    return response


def main():
    parser = argparse.ArgumentParser(
        description="AI Gold Agent - סוכן AI למסחר יומי בזהב",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
דוגמאות:
  python main.py                                    # סריקה מתמשכת כל 5 דקות + התראות
  python main.py --once                             # סריקה חד-פעמית
  python main.py --interval 120                     # סריקה כל 2 דקות
  python main.py --ask "תנתח את גרף ה-15 דקות"     # שאלה חופשית לסוכן
  python main.py --model qwen2.5:14b                # שימוש במודל אחר
        """
    )
    parser.add_argument("--once", action="store_true", help="סריקה חד-פעמית (ללא לולאה)")
    parser.add_argument("--interval", type=int, default=300, help="מרווח בין סריקות בשניות (ברירת מחדל: 300 = 5 דקות)")
    parser.add_argument("--ask", type=str, default=None, help="שאלה חופשית לסוכן")
    parser.add_argument("--model", type=str, default=None, help="מודל Ollama (ברירת מחדל: qwen2.5:7b-instruct)")
    parser.add_argument("--no-alerts", action="store_true", help="ללא התראות Windows")

    args = parser.parse_args()

    # הצגת באנר
    print_banner()

    # יצירת הסוכן
    model_name = args.model or os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct")
    print(f"{Colors.DIM}🔧 מאתחל את הסוכן עם מודל {model_name}...{Colors.RESET}")

    from agent import create_gold_agent, run_agent
    from alerts import parse_and_alert, send_scan_start_notification, send_scan_summary

    try:
        agent = create_gold_agent(model=model_name)
    except Exception as e:
        print(f"{Colors.RED}❌ שגיאה באתחול הסוכן: {e}{Colors.RESET}")
        print(f"   ודא ש-Ollama רץ ושהמודל {model_name} מותקן.")
        print(f"   הרץ: ollama pull {model_name}")
        sys.exit(1)

    print(f"{Colors.GREEN}✅ הסוכן מוכן!{Colors.RESET}")

    # מצב שאלה חופשית
    if args.ask:
        print_separator()
        print(f"{Colors.CYAN}💬 שאלה: {args.ask}{Colors.RESET}\n")
        print_thinking()
        try:
            response = run_agent(agent, args.ask)
            print_result(response)
        except Exception as e:
            print(f"{Colors.RED}❌ שגיאה: {e}{Colors.RESET}")
        return

    # מצב סריקה
    loop = not args.once
    interval_min = args.interval // 60

    if loop:
        print(f"{Colors.CYAN}ℹ️  מצב: סריקה מתמשכת כל {interval_min} דקות עם התראות Windows{Colors.RESET}")
        print(f"{Colors.CYAN}ℹ️  טיים-פריימים: 1m, 5m, 15m | Ctrl+C לעצירה{Colors.RESET}")
        if not args.no_alerts:
            send_scan_start_notification()
    else:
        print(f"{Colors.CYAN}ℹ️  מצב: סריקה חד-פעמית{Colors.RESET}")

    scan_count = 0
    total_alerts = 0

    try:
        while True:
            scan_count += 1
            print_separator()
            print(f"{Colors.BOLD}📊 סריקה #{scan_count} | סורק 3 טיים-פריימים...{Colors.RESET}\n")

            for tf in TIMEFRAMES:
                tf_label = TF_LABELS[tf]
                print(f"{Colors.DIM}⏱️  סורק גרף {tf_label} ({tf})...{Colors.RESET}")

                try:
                    response = scan_single_timeframe(agent, run_agent, tf)

                    # הצגת תוצאה
                    print(f"\n{Colors.CYAN}── {tf_label} ({tf}) ──{Colors.RESET}")
                    print(response)
                    print()

                    # שליחת התראה אם יש הזדמנות
                    if not args.no_alerts:
                        alerted = parse_and_alert(response, tf)
                        if alerted:
                            total_alerts += 1
                            print(f"{Colors.GREEN}🔔 התראה נשלחה!{Colors.RESET}\n")

                except Exception as e:
                    print(f"{Colors.RED}❌ שגיאה בסריקת {tf}: {e}{Colors.RESET}\n")

            # סיכום הסריקה
            print(f"{Colors.DIM}{'─' * 62}")
            print(f"✅ סריקה #{scan_count} הושלמה | {total_alerts} התראות נשלחו סה\"כ")
            print(f"{'─' * 62}{Colors.RESET}")

            if not loop:
                break

            # המתנה לסריקה הבאה
            next_scan = datetime.now().replace(second=0, microsecond=0)
            print(f"\n{Colors.DIM}⏳ סריקה הבאה בעוד {interval_min} דקות...{Colors.RESET}")
            time.sleep(args.interval)

    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}⏹️  הסריקה הופסקה.{Colors.RESET}")
        print(f"{Colors.DIM}   סה\"כ: {scan_count} סריקות | {total_alerts} התראות{Colors.RESET}")
        if not args.no_alerts and total_alerts > 0:
            send_scan_summary(total_alerts, scan_count)
        print(f"{Colors.GREEN}👋 להתראות! סחרו בחכמה.{Colors.RESET}\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
