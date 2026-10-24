# חיבור a1stl ל-Firebase Realtime Database דרך election_server.py

## מה בדקתי בקוד הציבורי
- `election_server.py` משתמש כרגע ב-`DATA_FILE = "elections_data.json"`.
- `load_data()` קורא מהקובץ המקומי ו-`save_data()` כותב אליו.
- `/api/results`, `/api/vote`, `/api/admin/reset` ו-`/api/admin/inject` מסתמכים על הפונקציות האלה.
- `index.html` קורא ל-`/api/results`, לכן אפשר לשמר את ממשק ה-API ולשנות את שכבת האחסון בשרת.

## שלב 1 — ודא את כתובת המסד
פתח:
https://console.firebase.google.com/u/0/project/planning-with-ai-d73ed/database

העתק את URL שמופיע בכותרת ה-Realtime Database. אל תנחש סיומת ואל תשתמש בכתובת ה-Console. שמור את ה-URL בלי `/.json` בסוף.

## שלב 2 — צור מפתח שירות לשרת
Firebase Console / Google Cloud Console → Project settings → Service accounts → Generate new private key.
הורד JSON ושמור אותו בסוד. **אל תעלה אותו ל-GitHub ואל תשלח אותו בצ'אט.**
ב-Render הגדר שתי Environment Variables:
- `FIREBASE_DATABASE_URL` = כתובת המסד שהעתקת מהכותרת
- `FIREBASE_SERVICE_ACCOUNT_JSON` = כל תוכן קובץ ה-JSON של מפתח השירות, כמחרוזת JSON תקינה

מפתח השירות מעניק הרשאות חזקות למסד. אין להטמיע אותו ב-HTML או במאגר.

## שלב 3 — עדכן את השרת
1. התקן תלות Firebase Admin SDK:
   `pip install -r requirements_firebase.txt`
   לחלופין, הוסף `firebase-admin>=6.5,<8` לקובץ `requirements.txt` הקיים.
2. פתח את `election_server.py`.
3. הוסף את קטע ה-import והאתחול מתוך `firebase_storage_patch.py.txt` אחרי ה-imports.
4. החלף את `load_data()` ואת `save_data()` הקיימות בגרסאות שמופיעות באותו קובץ.
5. השאר את שאר הקוד ללא שינוי בשלב הראשון. הנתיבים הקיימים אמורים להשתמש באחסון המרכזי דרך הפונקציות האלה.
6. Commit ו-Push ל-GitHub, ואז פרוס מחדש את שירות ה-Python ב-Render.

## שלב 4 — בדיקה
1. ב-Firebase Realtime Database → Data אמור להופיע הנתיב `election_data`.
2. פתח את האתר דרך כתובת שירות ה-Python, לא דרך GitHub Pages הסטטי.
3. הצבע פעם אחת ממכשיר A.
4. פתח את מסך התוצאות במכשיר B ובדוק שהמספר גדל.
5. ב-Firebase בדוק שהערכים תחת `election_data/votes` ו-`election_data/voted_devices` השתנו.
6. בצע redeploy והמתן לעלייה. ודא שהקולות נשארו.
7. בדוק איפוס רק לאחר ששמרת עותק של הנתונים, משום שאיפוס מוחק את נתוני הקלפי.

## מגבלות חשובות לפני שימוש
- הקוד הנוכחי משתמש ב-`db_lock`, שהוא מנעול בתוך תהליך Python יחיד. הפתרון הזה מתאים לשירות עם **instance יחיד**. אם מפעילים כמה instances במקביל, צריך להעביר את פעולת ההצבעה/איפוס ל-Firebase transaction אטומי כדי למנוע דריסת קולות במקביל.
- קוד הניהול הקיים משתמש ב-PIN קבוע בקוד (`2026` וגם `1234`) ונתיב inject מאפשר הוספת קולות לדוגמה. אין לחשוף את המערכת להצבעה ציבורית לפני הקשחת אימות המנהל, הסרת PIN חלש/קבוע והגבלת inject.
- זהו כלי הדגמה/סקר בלבד, לא מערכת לבחירות רשמיות. זיהוי לפי מזהה מכשיר או IP אינו מונע הצבעה כפולה באופן אמין.
- אין להגדיר את Firebase Rules כפתוחות לציבור. השרת המאומת באמצעות Admin SDK כותב למסד; הדפדפן לא צריך לקבל הרשאות כתיבה ישירות.
