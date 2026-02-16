"""
מודול תצוגה - הצגת אותות מסחר בעברית בצורה מסודרת ונוחה.
"""

import os
import sys
from datetime import datetime
from typing import List, Optional
from strategy import TradeSignal


# צבעים לטרמינל (ANSI)
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_BLUE = "\033[44m"
    DIM = "\033[2m"


def enable_windows_ansi():
    """מאפשר צבעי ANSI בטרמינל של Windows."""
    if sys.platform == "win32":
        os.system("")  # הפעלת ANSI ב-Windows
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except Exception:
            pass


def clear_screen():
    """ניקוי מסך."""
    os.system("cls" if os.name == "nt" else "clear")


def print_header():
    """הדפסת כותרת הסוכן."""
    enable_windows_ansi()
    header = f"""
{Colors.BOLD}{Colors.YELLOW}
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║        🏆  AI Gold Scanner - סוכן מסחר יומי בזהב  🏆       ║
║                                                              ║
║   מבוסס על אסטרטגיית AI Gold Institutional Scalper          ║
║   סריקה אוטומטית: 1 דקה | 5 דקות | 15 דקות                ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
{Colors.RESET}"""
    print(header)


def print_scanning_status(timeframe: str, current_price: Optional[float] = None):
    """הצגת סטטוס סריקה."""
    tf_labels = {"1m": "⏱️  דקה", "5m": "⏱️  5 דקות", "15m": "⏱️  15 דקות"}
    label = tf_labels.get(timeframe, timeframe)

    price_str = f" | מחיר: ${current_price:,.2f}" if current_price else ""
    now = datetime.now().strftime("%H:%M:%S")

    print(f"{Colors.DIM}[{now}] סורק גרף {label}{price_str}...{Colors.RESET}")


def print_no_signal(timeframe: str):
    """הצגת הודעה כשאין אות."""
    tf_labels = {"1m": "דקה", "5m": "5 דקות", "15m": "15 דקות"}
    label = tf_labels.get(timeframe, timeframe)
    print(f"{Colors.DIM}   ↳ גרף {label}: אין הזדמנות כרגע{Colors.RESET}")


def print_signal(signal: TradeSignal):
    """הצגת אות מסחר מלא בעברית."""

    if signal.signal_type == "LONG":
        color = Colors.GREEN
        bg_color = Colors.BG_GREEN
        emoji = "🟢"
        type_he = "לונג (קנייה)"
    else:
        color = Colors.RED
        bg_color = Colors.BG_RED
        emoji = "🔴"
        type_he = "שורט (מכירה)"

    tf_labels = {"1m": "דקה", "5m": "5 דקות", "15m": "15 דקות"}
    tf_label = tf_labels.get(signal.timeframe, signal.timeframe)

    confidence_bar = _build_confidence_bar(signal.confidence)
    timestamp_str = signal.timestamp.strftime("%Y-%m-%d %H:%M") if hasattr(signal.timestamp, 'strftime') else str(signal.timestamp)

    output = f"""
{Colors.BOLD}{color}
╔══════════════════════════════════════════════════════════════╗
║  {emoji}  אות {type_he} זוהה!  {emoji}                            
╠══════════════════════════════════════════════════════════════╣
║                                                              
║  ⏰ זמן:        {timestamp_str}                  
║  📊 טיים-פריים: {tf_label}                                 
║  📈 ביטחון:     {confidence_bar} {signal.confidence:.0f}%               
║                                                              
╠══════════════════════════════════════════════════════════════╣
║  💰 מחיר כניסה:        ${signal.entry_price:>10,.2f}                
║  🛑 סטופ-לוס:          ${signal.stop_loss:>10,.2f}                
║  🎯 יעד 1 (1:1):       ${signal.take_profit_1:>10,.2f}                
║  🎯 יעד 2 (1:2):       ${signal.take_profit_2:>10,.2f}                
║  🎯 יעד 3 (1:3):       ${signal.take_profit_3:>10,.2f}                
║                                                              
║  📐 סיכון:  ${signal.risk_points:>8,.2f}                          
║  💎 רווח:   ${signal.reward_points:>8,.2f}                          
║  ⚖️  R:R:    1:{signal.risk_reward_ratio:.1f}                              
╠══════════════════════════════════════════════════════════════╣
║  📋 אינדיקטורים:                                            
║     EMA 50:  {signal.indicators.get('EMA_fast', 'N/A')}                 
║     EMA 200: {signal.indicators.get('EMA_slow', 'N/A')}                
║     ATR:     {signal.indicators.get('ATR', 'N/A')}                      
║     RSI:     {signal.indicators.get('RSI', 'N/A')}                      
║     VWAP:    {signal.indicators.get('VWAP', 'N/A')}                     
╚══════════════════════════════════════════════════════════════╝{Colors.RESET}

{Colors.CYAN}📝 ניתוח מפורט:{Colors.RESET}
{signal.description_he}
{'═' * 62}
"""
    print(output)


def print_summary(signals: List[TradeSignal]):
    """הצגת סיכום של כל האותות שנמצאו."""
    if not signals:
        print(f"\n{Colors.YELLOW}📭 לא נמצאו הזדמנויות מסחר בסריקה הנוכחית.{Colors.RESET}")
        return

    print(f"\n{Colors.BOLD}{Colors.CYAN}{'═' * 62}")
    print(f"📊  סיכום סריקה - נמצאו {len(signals)} הזדמנויות")
    print(f"{'═' * 62}{Colors.RESET}")

    for i, sig in enumerate(signals, 1):
        emoji = "🟢" if sig.signal_type == "LONG" else "🔴"
        color = Colors.GREEN if sig.signal_type == "LONG" else Colors.RED
        tf_labels = {"1m": "1D", "5m": "5D", "15m": "15D"}
        tf = tf_labels.get(sig.timeframe, sig.timeframe)

        print(f"{color}  {i}. {emoji} {sig.signal_type} [{tf}] "
              f"כניסה: ${sig.entry_price:,.2f} → "
              f"יעד: ${sig.take_profit_2:,.2f} | "
              f"SL: ${sig.stop_loss:,.2f} | "
              f"ביטחון: {sig.confidence:.0f}%{Colors.RESET}")

    print(f"{Colors.DIM}{'═' * 62}{Colors.RESET}\n")


def print_error(message: str):
    """הצגת הודעת שגיאה."""
    print(f"\n{Colors.RED}❌ שגיאה: {message}{Colors.RESET}")


def print_info(message: str):
    """הצגת הודעת מידע."""
    print(f"{Colors.CYAN}ℹ️  {message}{Colors.RESET}")


def _build_confidence_bar(confidence: float, length: int = 20) -> str:
    """בניית בר ביטחון ויזואלי."""
    filled = int(confidence / 100 * length)
    empty = length - filled

    if confidence >= 75:
        color = Colors.GREEN
    elif confidence >= 50:
        color = Colors.YELLOW
    else:
        color = Colors.RED

    return f"{color}{'█' * filled}{'░' * empty}{Colors.RESET}"
