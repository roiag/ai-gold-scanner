# 🏆 AI Gold Agent - סוכן AI למסחר יומי בזהב

סוכן AI אמיתי (**LangGraph + GPT-4o**) המתמחה במסחר יומי בזהב.  
הסוכן סורק גרפים, מנתח אינדיקטורים, **חושב**, ומחליט בעצמו אם יש הזדמנות מסחר.

## 🤖 למה זה AI Agent ולא סקריפט?

| | סקריפט רגיל | AI Agent (הפרויקט הזה) |
|---|---|---|
| **קבלת החלטות** | `if/else` קשיח | LLM חושב ומנתח |
| **גמישות** | לוגיקה קבועה | מבין הקשר ומסתגל |
| **הסברים** | הודעות מוכנות מראש | הסוכן כותב ניתוח ייחודי |
| **אינטראקציה** | פרמטרים בלבד | אפשר לשאול שאלות חופשיות |
| **ארכיטקטורה** | פונקציות ליניאריות | LangGraph ReAct Agent עם Tools |

## 🏗️ ארכיטקטורה

```
User → main.py → LangGraph Agent (GPT-4o)
                        │
                        ├── Tool: get_current_gold_price()
                        ├── Tool: get_gold_chart(timeframe)
                        ├── Tool: calculate_indicators(timeframe)
                        └── Tool: calculate_trade_levels(entry, type, atr)
                        │
                        ▼
                  LLM מנתח את כל הנתונים
                  ומחזיר תשובה בעברית
```

הסוכן עובד בלולאת **ReAct** (Reason + Act):
1. **חושב** - מה הצעד הבא שצריך?
2. **פועל** - קורא ל-Tool מתאים
3. **צופה** - מקבל את התוצאה
4. **חוזר על 1-3** עד שיש מספיק מידע
5. **מסכם** - כותב ניתוח מפורט בעברית

## ⚡ התקנה מהירה

```bash
# 1. התקנת תלויות
pip install -r requirements.txt

# 2. הגדרת API key
# צור קובץ .env עם:
echo OPENAI_API_KEY=sk-your-key-here > .env

# 3. הרצה
python main.py
```

## 🚀 שימוש

```bash
# סריקה חד-פעמית - הסוכן סורק 3 טיים-פריימים
python main.py

# סריקה מתמשכת כל דקה
python main.py --loop

# סריקה כל 2 דקות
python main.py --loop --interval 120

# שאלה חופשית לסוכן
python main.py --ask "מה אתה חושב על גרף ה-5 דקות?"
python main.py --ask "האם יש מגמה ברורה עכשיו?"
python main.py --ask "תסביר לי את מצב ה-RSI בכל הטיים-פריימים"
```

## 📊 האסטרטגיה

מבוססת על **AI Gold Institutional Scalper**:

1. **EMA 50/200** - זיהוי מגמה מוסדית
2. **Pullback Continuation** - כניסה בנסיגה
3. **ATR Dynamic Stop** - סטופ-לוס מותאם תנודתיות
4. **Volume Confirmation** - אישור נפח מוסדי
5. **RSI + VWAP** - אישורי מומנטום

## 📁 מבנה הפרויקט

```
goldScanner/
├── main.py          # נקודת כניסה + CLI
├── agent.py         # LangGraph Agent + System Prompt
├── tools.py         # כלי הסוכן (data, indicators, levels)
├── .env             # OPENAI_API_KEY (לא ב-Git)
├── .env.example     # דוגמה ל-.env
├── requirements.txt # תלויות
└── README.md        # תיעוד
```

## ⚠️ הבהרה

כלי זה הוא לצורכי לימוד וניתוח בלבד. אין להתייחס לאותות כהמלצה פיננסית.
