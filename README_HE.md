# a1stl — גרסה עדכנית לפריסה והצבעה ממספר מכשירים

## קבצים
- `election_server.py` — שרת Python עם Firebase Realtime Database.
- `index.html` — הממשק המקורי שסופק, ללא כותרות/שורות עטיפה של ייצוא.
- `requirements.txt` — תלות Firebase Admin SDK.
- `render.yaml` — הגדרת Render.
- `.gitignore` — התעלמות מקובצי סודות.

## פריסה
1. העלה/החלף במאגר GitHub `amitaicohen/a1stl` את `election_server.py` ואת `index.html` שבחבילה.
2. הוסף `requirements.txt` ו-`render.yaml`. אם כבר קיים `requirements.txt`, מזג את תלות Firebase עם התלויות הקיימות.
3. ב-Render צור Web Service למאגר. Build command: `pip install -r requirements.txt`; Start command: `python election_server.py`.
4. ב-Render → Environment הוסף:
   - `FIREBASE_DATABASE_URL` — כתובת ה-Realtime Database המדויקת מ-Firebase Console.
   - `FIREBASE_SERVICE_ACCOUNT_JSON` — כל תוכן קובץ Service Account JSON, כערך משתנה.
5. צור את מפתח השירות ב-Firebase Console → Project settings → Service accounts. שמור אותו בסוד: לעולם אל תעלה אותו ל-GitHub ואל תשלח אותו בצ'אט.
6. בצע Deploy. כתובת השירות של Render תהיה כתובת האתר וה-API. שתף את כתובת Render עם המצביעים.
7. בדיקה: פתח `https://YOUR-SERVICE.onrender.com/api/results` וודא שמתקבל JSON עם `success: true`. לאחר מכן בדוק בשני מכשירים.

## מה תוקן
- התאמה ל-`PORT` ש-Render מקצה.
- הגשת `index.html` כשורש האתר.
- הצבעה ועדכון מונים בתוך Firebase transaction, כך שהכתיבה תהיה אטומית גם כשיש בקשות במקביל.
- החזרת `reset_id` בתוצאות ואיפוס אטומי.
- ביטול נתיב הזרקת הצבעות הדמה בפרסום.

## אבטחה
- בקוד המנהל עדיין קיימים קודי PIN קבועים `2026` ו-`1234`; החלף אותם לפני פרסום לציבור.
- מזהה דפדפן אינו מונע הצבעה חוזרת ממכשיר אחר או לאחר מחיקת נתוני דפדפן. אין להשתמש במערכת לבחירות רשמיות.
- החבילה אינה מבצעת Deploy לחשבונות שלך ואינה מוכיחה שהגדרות Firebase נכונות; יש לבצע את ההגדרות ולבדוק את השירות בפועל.
