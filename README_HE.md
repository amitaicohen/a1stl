# חיבור a1stl ל-Firebase דרך Render

החבילה הזו כוללת קובצי הגדרה והוראות. היא **אינה** כוללת גרסה מלאה ומאומתת של `election_server.py`, כי צריך לבצע את השינויים בקובץ הקיים כדי לשמר את כל נתיבי ה-API והלוגיקה של ההצבעה.

## מה צריך להיות בפרויקט
- `election_server.py` — הקובץ הקיים שלך
- `requirements.txt` — אפשר למזג עם הקיים; אל תדרוס תלויות קיימות
- `render.yaml` — הגדרת שירות Render
- `.gitignore` — מונע העלאת קובצי סודות

## שלב 1 — הוסף את התלות
פתח את `requirements.txt` שבמאגר GitHub. אם אין כזה, צור אותו. הוסף שורה:

    firebase-admin>=6.5,<8

אל תמחק תלויות קיימות אחרות.

## שלב 2 — הוסף את הגדרות Firebase ל-elections_server.py
פתח את `election_server.py`.

א. ליד שאר ה-imports הוסף את הקוד הבא:

    import os
    import json
    import firebase_admin
    from firebase_admin import credentials, db as firebase_db

ב. אחרי כל ה-imports ולפני הפעלת השרת, הוסף:

    _service_account_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")
    _database_url = os.environ.get("FIREBASE_DATABASE_URL")

    if not _service_account_json or not _database_url:
        raise RuntimeError(
            "Missing FIREBASE_SERVICE_ACCOUNT_JSON or FIREBASE_DATABASE_URL"
        )

    _credential = credentials.Certificate(json.loads(_service_account_json))
    firebase_admin.initialize_app(
        _credential,
        {"databaseURL": _database_url}
    )
    FIREBASE_ROOT = firebase_db.reference("election_data")

ג. מצא את הפונקציות `load_data()` ו-`save_data()` הקיימות. החלף רק את שתי הפונקציות האלה בקוד הבא, ושמור את שמות הפונקציות כדי שכל נתיבי ה-API הקיימים ימשיכו להשתמש בהן:

    def load_data():
        data = FIREBASE_ROOT.get()
        if not isinstance(data, dict):
            data = {
                "votes": [],
                "voted_devices": [],
                "voted_ips": [],
                "reset_id": 0
            }
            FIREBASE_ROOT.set(data)
        return data

    def save_data(data):
        FIREBASE_ROOT.set(data)

**חשוב:** יש לוודא שהמבנה הראשוני תואם בדיוק למבנה שהקוד הקיים מצפה לו. אם הקוד הקיים כולל שדות נוספים, הוסף אותם למילון הראשוני לפני פרסום.

## שלב 3 — הגן על קובץ המפתחות
קובץ JSON פרטי של Service Account לא מעלים ל-GitHub. בחבילה יש `.gitignore` שמכסה שמות נפוצים, אבל עדיין בדוק ידנית לפני commit.

## שלב 4 — פרסום ב-Render
1. צור חשבון ב-https://render.com/ והתחבר ל-GitHub.
2. בחר New → Web Service ובחר את המאגר `amitaicohen/a1stl`.
3. Runtime: Python.
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `python election_server.py`
6. הוסף Environment Variables:
   - `FIREBASE_DATABASE_URL` = כתובת ה-Realtime Database המדויקת מה-Firebase Console
   - `FIREBASE_SERVICE_ACCOUNT_JSON` = כל תוכן קובץ ה-Service Account JSON, כמחרוזת JSON אחת. אין להוסיף מרכאות חיצוניות מעבר לתוכן הקובץ.
7. צור את השירות והמתן לפריסה. אם יש שגיאה, בדוק Logs.

## שלב 5 — בדיקה
- פתח את כתובת השירות ב-Render ובדוק אם נתיב הבסיס מגיב (ייתכן שהשרת לא מציג עמוד בבסיס).
- בדוק את ה-endpoint `/api/results` בכתובת Render.
- יש לעדכן את האתר הסטטי כך שבקשות API יפנו לכתובת Render. כרגע צריך לבדוק את `index.html` ולוודא שכל `fetch('/api/...')` או נתיב יחסי אחר הוחלף בבסיס URL של Render.
- פתח את האתר בשני דפדפנים, הצבע במכשיר אחד ובדוק שהשני רואה את התוצאה.

## אזהרות חשובות
- הקוד הקיים משתמש בנעילה מקומית (`threading.Lock`) ובדיקות הצבעה כפולה מבוססות נתונים. נעילה מקומית אינה מספיקה כאשר יש כמה תהליכי שרת, והפעולה read-modify-write על Firebase אינה אטומית. לצורך פיילוט קטן, הגדר instance אחד; עבור מערכת אמינה צריך להשתמש ב-Firebase transactions או במנגנון אטומי.
- אם הקוד מכיל PIN מנהל קבוע או endpoint להזרקת הצבעות בדיקה, יש להקשיח/להסיר אותם לפני שימוש ציבורי.
- אין להשתמש בפתרון הזה לבחירות רשמיות או לתהליך שבו נדרשת שלמות הצבעה מאומתת.
