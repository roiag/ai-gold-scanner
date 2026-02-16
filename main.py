"""
AI Gold Scanner - נקודת כניסה ראשית.

סוכן AI (LangGraph + GPT-4o) המתמחה במסחר יומי בזהב.
סורק גרפים בזמן אמת ומחפש הזדמנויות לונג/שורט.

שימוש:
    python main.py                          # סריקה חד-פעמית
    python main.py --loop                   # סריקה מתמשכת כל 60 שניות
    python main.py --loop --interval 120    # סריקה כל 2 דקות
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

def main():
    parser = argparse.ArgumentParser(
        description="AI Gold Agent - סוכן AI למסחר יומי בזהב",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
דוגמאות:
  python main.py                                    # סריקה חד-פעמית
  python main.py --loop                             # סריקה מתמשכת (כל 60 שניות)
  python main.py --loop --interval 120              # סריקה כל 2 דקות
  python main.py --ask "תנתח את גרף ה-15 דקות"     # שאלה חופשית לסוכן
        """
    )
    parser.add_argument("--loop", action="store_true", help="סריקה מתמשכת")
    parser.add_argument("--interval", type=int, default=60, help="מרווח בין סריקות בשניות (ברירת מחדל: 60)")
    parser.add_argument("--ask", type=str, default=None, help="שאלה חופשית לסוכן")
    parser.add_argument("--model", type=str, default=None, help="מודל Ollama (ברירת מחדל: qwen2.5:7b-instruct)")

    args = parser.parse_args()

    # הצגת באנר
    print_banner()

# יצירת הסוכן
    model_name = args.model or os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct")
    print(f"{Colors.DIM}🔧 מאתחל את הסוכן עם מודל {model_name}...{Colors.RESET}")

    from agent import create_gold_agent, run_agent
    try:
        agent = create_gold_agent(model=model_name)
    except Exception as e:
        print(f"{Colors.RED}❌ שגיאה באתחול הסוכן: {e}{Colors.RESET}")
        print(f"   ודא ש-Ollama רץ ושהמודל {model_name} מותקן.")
        print(f"   הרץ: ollama pull {model_name}")
        sys.exit(1)

    print(f"{Colors.GREEN}✅ הסוכן מוכן!{Colors.RESET}")

    if args.loop:
        print(f"{Colors.CYAN}ℹ️  מצב סריקה מתמשכת כל {args.interval} שניות. Ctrl+C לעצירה.{Colors.RESET}")

    scan_count = 0

    try:
        while True:
            scan_count += 1
            print_separator()

            if args.ask:
                print(f"{Colors.CYAN}💬 שאלה: {args.ask}{Colors.RESET}\n")

            print_thinking()

            try:
                user_msg = args.ask  # None = סריקה רגילה
                response = run_agent(agent, user_msg)
                print_result(response)
            except Exception as e:
                print(f"{Colors.RED}❌ שגיאה: {e}{Colors.RESET}")

            if not args.loop:
                break

            # אחרי שאלה חופשית לא ממשיכים בלולאה
            if args.ask:
                break

            print(f"\n{Colors.DIM}⏳ סריקה הבאה בעוד {args.interval} שניות...{Colors.RESET}")
            time.sleep(args.interval)

    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}⏹️  הסריקה הופסקה.{Colors.RESET}")
        print(f"{Colors.GREEN}👋 להתראות! סחרו בחכמה.{Colors.RESET}\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
