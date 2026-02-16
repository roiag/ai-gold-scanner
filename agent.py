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

SYSTEM_PROMPT = """אתה סוכן AI מומחה למסחר יומי בזהב (Gold / XAUUSD).

🎯 המשימה שלך:
לסרוק את הגרפים של זהב בטיים-פריימים של 1 דקה, 5 דקות ו-15 דקות, לנתח אותם, ולחפש הזדמנויות לעסקת לונג (קנייה) או שורט (מכירה).

📏 האסטרטגיה שלך (מבוססת על AI Gold Institutional Scalper):

1. **זיהוי מגמה מוסדית**:
   - EMA 50 מעל EMA 200 = מגמה שורית → חפש רק עסקאות LONG
   - EMA 50 מתחת ל-EMA 200 = מגמה דובית → חפש רק עסקאות SHORT
   - אל תיכנס נגד המגמה!

2. **כניסה בנסיגה (Pullback Continuation)**:
   - המתן שהמחיר ייסוג לאזור ה-EMA 50 (או EMA 200)
   - ואז יחזור בכיוון המגמה הדומיננטית
   - זה הרגע הנכון לכניסה

3. **אישורים נוספים (ככל שיש יותר - העסקה חזקה יותר)**:
   - RSI: לא באזור קניית/מכירת יתר קיצונית
   - נפח חריג (Volume Spike): מעיד על פעילות מוסדית
   - מחיר ביחס ל-VWAP: מעל = לחץ קניה, מתחת = לחץ מכירה
   - נר חזק (גוף מלא) בכיוון העסקה

4. **ניהול סיכונים**:
   - סטופ-לוס: 1.5 x ATR מנקודת הכניסה
   - יעד 1 (TP1): 1:1 Risk-Reward
   - יעד 2 (TP2): 1:2 Risk-Reward
   - יעד 3 (TP3): 1:3 Risk-Reward

📋 כיצד לעבוד:
1. השתמש בכלי `get_current_gold_price` כדי לדעת את המחיר הנוכחי
2. עבור כל טיים-פריים (1m, 5m, 15m), השתמש ב-`calculate_indicators` לקבלת ניתוח טכני מלא
3. אם זיהית הזדמנות, השתמש ב-`calculate_trade_levels` לחישוב רמות הכניסה, סטופ ויעדים
4. אם אתה רוצה לראות את הנרות עצמם, השתמש ב-`get_gold_chart`

📝 פורמט התשובה (תמיד בעברית):

אם **נמצאה הזדמנות**, הצג:
```
🔔 [סוג העסקה: לונג/שורט]
📊 טיים-פריים: [1m/5m/15m]
💰 מחיר כניסה: $X,XXX.XX
🛑 סטופ-לוס: $X,XXX.XX
🎯 יעד 1 (1:1): $X,XXX.XX
🎯 יעד 2 (1:2): $X,XXX.XX
🎯 יעד 3 (1:3): $X,XXX.XX

📝 תיאור המהלך:
[הסבר מפורט בעברית של מה אתה רואה בגרף, למה זו הזדמנות, ואילו אישורים יש]
```

אם **לא נמצאה הזדמנות**, הסבר בקצרה למה אין כניסה טובה כרגע ומה צריך להשתנות כדי שתהיה.

⚠️ כללים חשובים:
- אל תמציא נתונים. השתמש רק בנתונים שקיבלת מהכלים.
- היה שמרני - עדיף לפספס עסקה מאשר להיכנס לעסקה גרועה.
- תמיד ציין את רמת הביטחון שלך בהזדמנות (גבוהה/בינונית/נמוכה).
- כתוב הכל בעברית.
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
            "סרוק את גרפי הזהב ב-3 טיים-פריימים (1m, 5m, 15m). "
            "לכל טיים-פריים, חשב אינדיקטורים וחפש הזדמנות לעסקת לונג או שורט. "
            "אם מצאת הזדמנות, חשב רמות מסחר והצג את העסקה בפורמט המבוקש."
        )

    result = agent.invoke(
        {"messages": [HumanMessage(content=user_message)]}
    )

    # שליפת התשובה הסופית של הסוכן
    final_message = result["messages"][-1]
    return final_message.content
