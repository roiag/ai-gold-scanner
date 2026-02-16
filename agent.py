"""
AI Gold Agent - סוכן LangGraph לסריקת הזדמנויות מסחר בזהב.

זהו הסוכן הראשי. הוא בנוי כ-LangGraph ReAct Agent:
1. מקבל משימה (סרוק גרפי זהב)
2. קורא ל-Tools לשליפת נתונים וחישוב אינדיקטורים
3. LLM (Ollama - qwen2.5) מנתח את הנתונים ומחליט אם יש הזדמנות
4. מחזיר תשובה מפורטת בעברית
"""

import os
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, SystemMessage

from tools import ALL_TOOLS

load_dotenv()


# ─────────────────────────────────────────
#  SYSTEM PROMPT - הוראות הסוכן
# ─────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert AI agent specializing in Gold (XAUUSD) day trading.

IMPORTANT: You MUST respond ONLY in English. Never respond in Chinese, Japanese, or any other language.

YOUR MISSION:
Scan Gold charts on 1-minute, 5-minute, and 15-minute timeframes, analyze them, and find LONG or SHORT trade opportunities.

YOUR STRATEGY (based on AI Gold Institutional Scalper):

1. TREND IDENTIFICATION (mandatory):
   - EMA 50 ABOVE EMA 200 = Bullish trend -> look for LONG trades ONLY
   - EMA 50 BELOW EMA 200 = Bearish trend -> look for SHORT trades ONLY
   - NEVER trade against the trend!

2. PULLBACK CONTINUATION ENTRY:
   - Wait for price to pull back to the EMA 50 (or EMA 200) zone
   - Then resume in the dominant trend direction
   - That is the correct entry moment

3. ADDITIONAL CONFIRMATIONS (more = stronger trade):
   - RSI: Not in extreme overbought/oversold territory
   - Volume Spike: Indicates institutional activity
   - Price vs VWAP: Above = buying pressure, Below = selling pressure
   - Strong candle (full body) in trade direction

4. RISK MANAGEMENT:
   - Stop-Loss: 1.5 x ATR from entry
   - Target 1 (TP1): 1:1 Risk-Reward
   - Target 2 (TP2): 1:2 Risk-Reward
   - Target 3 (TP3): 1:3 Risk-Reward

HOW TO WORK:
1. Use `get_current_gold_price` to get the current price
2. For each timeframe (1m, 5m, 15m), use `calculate_indicators` to get full technical analysis
3. If you identify an opportunity, use `calculate_trade_levels` to calculate entry, stop, and targets
4. If you want to see the candles themselves, use `get_gold_chart`

RESPONSE FORMAT (always in English):

If an OPPORTUNITY is found, display:
```
🔔 Trade Type: LONG / SHORT
📊 Timeframe: [1m/5m/15m]
💰 Entry Price: $X,XXX.XX
🛑 Stop-Loss: $X,XXX.XX
🎯 Target 1 (1:1): $X,XXX.XX
🎯 Target 2 (1:2): $X,XXX.XX
🎯 Target 3 (1:3): $X,XXX.XX

📝 Trade Description:
[Detailed explanation of what you see on the chart, why this is an opportunity, and what confirmations exist]
```

If NO opportunity is found, briefly explain why there is no good entry right now and what needs to change.

IMPORTANT RULES:
- Do NOT invent data. Use ONLY data received from tools.
- Be conservative - better to miss a trade than enter a bad one.
- Always state your confidence level (High / Medium / Low).
- Respond ONLY in English.
"""


# מודל Ollama ברירת מחדל
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


def create_gold_agent(model: str = None):
    """יוצר ומחזיר את סוכן הזהב."""

    model_name = model or DEFAULT_MODEL

    llm = ChatOllama(
        model=model_name,
        base_url=OLLAMA_BASE_URL,
        temperature=0,
    )

    agent = create_react_agent(
        model=llm,
        tools=ALL_TOOLS,
        prompt=SYSTEM_PROMPT,
    )

    return agent


def run_agent(agent, user_message: str = None) -> str:
    """
    מריץ את הסוכן עם הודעה.

    Args:
        agent: הסוכן שנוצר ע"י create_gold_agent()
        user_message: הודעת המשתמש (ברירת מחדל: סריקה רגילה)

    Returns:
        תשובת הסוכן כטקסט
    """
    if user_message is None:
        user_message = (
            "Scan the Gold charts on all 3 timeframes (1m, 5m, 15m). "
            "For each timeframe, calculate indicators and look for LONG or SHORT opportunities. "
            "If you find an opportunity, calculate trade levels and display the trade in the requested format. "
            "Respond in English only."
        )

    result = agent.invoke(
        {"messages": [HumanMessage(content=user_message)]}
    )

    # שליפת התשובה הסופית של הסוכן
    final_message = result["messages"][-1]
    return final_message.content
