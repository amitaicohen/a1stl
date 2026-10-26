
#!/usr/bin/env python3
"""
שרת בחירות 2026 לכנסת ה-26 (גרסה 4.0 - Multi-Device Concurrency & Live Sync)
שרת HTTP ו-REST API מבוסס ThreadingTCPServer עם סנכרון רשת מלא.
תומך בהצבעה סימולטנית ממאות מכשירים במקביל (טלפונים, טאבלטים ומחשבים) לאותן תוצאות אמת.
"""

import http.server
import socketserver
import urllib.parse
import json
import os
import sys
import threading
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, db as firebase_db

PORT = 8000
DATA_FILE = "elections_data.json"
HTML_FILE = "index.html"

# מנעול לסנכרון כתיבה בטוחה לקובץ הנתונים בריבוי נימים (Thread-Safety)
db_lock = threading.Lock()

PARTIES = [
  {
    "id": "mahal",
    "letter": "מחל",
    "name": "הליכוד בהנהגת בנימין נתניהו לראשות הממשלה",
    "short": "הליכוד",
    "leader": "בנימין נתניהו",
    "color": "#1877f2",
    "bloc": "right",
    "ballot_sub": "הליכוד בהנהגת בנימין נתניהו לראשות הממשלה",
    "surplus_partner": "tet",
    "candidates": [
      "1. בנימין נתניהו (יו\"ר הליכוד וראש הממשלה)",
      "2. אליהו כהן (מקום 1 בפריימריז, שר החוץ והאנרגיה)",
      "3. אמיר אוחנה (יו\"ר הכנסת)",
      "4. יריב גדעון לוין (שר המשפטים וסגן ראש הממשלה)",
      "5. מרים (מירי) רגב (שרת התחבורה והבטיחות בדרכים)",
      "6. ישראל כ\"ץ (שר הביטחון)",
      "7. גדעון משה סער (יו\"ר הימין הממלכתי / שר החוץ)",
      "8. אופיר כ\"ץ (יו\"ר הקואליציה ויו\"ר סיעת הליכוד)",
      "9. טליק (טלי) גואילי (אמו של רן גואילי הי\"ד, שריון יו\"ר)",
      "10. יואב קיש (שר החינוך)"
    ],
    "platform": {
      "security": "הכרעה צבאית מוחלטת נגד הטרור, פירוק חמאס, שמירת חופש פעולה ביטחוני בכל הגזרות, התנגדות למדינה פלסטינית והרחבת הסכמי אברהם.",
      "economy": "כלכלת שוק חופשי, עידוד יזמות והייטק, הפחתת רגולציה ומסים, השקעה מסיבית בתשתיות לאומיות והורדת יוקר המחיה.",
      "education": "חיזוק החינוך הלאומי והציוני, הרחבת חינוך חינם לגילאי 0-3, שיפור מעמד המורה ומצוינות מדעית וטכנולוגית.",
      "enlistment": "הסדרת מעמד בני הישיבות בהסכמה והדרגתיות, שילוב מסלולים ייעודיים לחרדים בצה\"ל ובשירות אזרחי תוך שימור עולם התורה."
    }
  },
  {
    "id": "rak",
    "letter": "רק",
    "name": "ביחד בראשות נפתלי בנט",
    "short": "ביחד",
    "leader": "נפתלי בנט ויאיר לפיד",
    "color": "#2563eb",
    "bloc": "center_left",
    "ballot_sub": "ביחד בראשות נפתלי בנט (בנט 2026 ויש עתיד)",
    "surplus_partner": "derech",
    "candidates": [
      "1. נפתלי בנט (יו\"ר הרשימה, ראש ממשלת ישראל לשעבר)",
      "2. יאיר לפיד (ראש הממשלה ושר החוץ לשעבר, יו\"ר יש עתיד)",
      "3. קרן טרנר אייל (מנכ\"לית משרדי האוצר והתחבורה לשעבר)",
      "4. מירב בן ארי (חברת כנסת ויו\"ר ועדת ביטחון פנים לשעבר)",
      "5. לירן אבישר בן חורין (מנכ\"לית משרד התקשורת לשעבר)",
      "6. אלוף במיל' נעם תיבון (מפקד הגיס הצפוני לשעבר ואיש ביטחון)",
      "7. מיכל הירש נגרי (מנכ\"לית עיריית רעננה לשעבר ואשת ניהול)",
      "8. איתן גינזבורג (חבר כנסת, סגן יו\"ר הכנסת וראש עיריית רעננה לשעבר)",
      "9. מירב כהן (שרת השוויון החברתי לשעבר)",
      "10. יונתן שלו (איש עסקים, יזם ופעיל חברתי)"
    ],
    "platform": {
      "security": "יוזמה והתקפיות ביטחונית, הכאת ראש התמנון האיראני, שיקום עוטף עזה והצפון, ובניית צה\"ל כצבא גדול, טכנולוגי וקטלני.",
      "economy": "כלכלה חופשית ויזמית, רפורמות עומק להפחתת מיסוי, שבירת קרטלים ומכסי מגן, והובלה עולמית בבינה מלאכותית ואנרגיה.",
      "education": "זינוק למצוינות מתמטית וטכנולוגית, חיזוק ערכי הציונות והערבות ההדדית, ושילוב לימודי ליב\"ה ומקצועות העתיד בכל זרמי החינוך.",
      "enlistment": "הרחבת שורות צה\"ל בדחיפות: גיוס חטיבות חרדיות לוחמות, אכיפת חוק גיוס אפקטיבי ללא פשרות, והוקרה חסרת תקדים ללוחמים."
    }
  },
  {
    "id": "ken",
    "letter": "כן",
    "name": "כחול לבן בהנהגת בני גנץ",
    "short": "כחול לבן",
    "leader": "בני גנץ",
    "color": "#002b49",
    "bloc": "center_left",
    "ballot_sub": "כחול לבן בהנהגת בני גנץ",
    "surplus_partner": "emet",
    "candidates": [
      "1. בני גנץ (יו\"ר המפלגה, רמטכ\"ל ושר הביטחון לשעבר)",
      "2. פנינה תמנו־שטה (שרת העלייה והקליטה לשעבר וחברת כנסת)",
      "3. ד\"ר עליזה בלוך (ראשת עיריית בית שמש לשעבר)",
      "4. רועי קונקול (לוחם מילואים, יועץ תקשורת ואיש ציבור)",
      "5. רותם אבידר־צאליק (עורכת דין ופעילה חברתית)",
      "6. אלון שוסטר (סגן שר הביטחון ושר החקלאות לשעבר)",
      "7. אל\"מ במיל' מופיד מרעי (חבר כנסת לשעבר וראש מועצת חורפיש)",
      "8. יהודית אוליאל (אשת ציבור וחינוך)",
      "9. אריאל בזיז (פעיל חברתי ואיש עשייה)",
      "10. מוריה סילפן (משפטנית ופעילת ציבור)"
    ],
    "platform": {
      "security": "עליונות ביטחונית נחרצת, חיזוק צה\"ל וזרועות הביטחון, שמירה על בקעת הירדן וגושי ההתיישבות, ומדיניות יוזמת לשימור בריתות אזוריות.",
      "economy": "כלכלה אחראית וממלכתית, השקעה במנועי צמיחה בפריפריה, מלחמה בריכוזיות, ותמיכה חסרת תקדים במשרתי המילואים ובמשפחותיהם.",
      "education": "ממלכתיות בחינוך, חיזוק החינוך המדעי והמקצועי, העלאת שכר המורים, והקניית מיומנויות תעסוקה ומדע לכלל המגזרים.",
      "enlistment": "מתווה שירות ישראלי רחב: מנהלת שירות לאומית שתחייב גיוס של חרדים וערבים לצבא או לארגוני הצלה וחסד, ושלילת הטבות ממי שאינו משרת."
    }
  },
  {
    "id": "lamed",
    "letter": "ל",
    "name": "ישראל ביתנו בראשות אביגדור ליברמן",
    "short": "ישראל ביתנו",
    "leader": "אביגדור ליברמן",
    "color": "#005596",
    "bloc": "right",
    "ballot_sub": "ישראל ביתנו בראשות אביגדור ליברמן",
    "surplus_partner": "day",
    "candidates": [
      "1. אביגדור ליברמן (יו\"ר המפלגה ושר האוצר והביטחון לשעבר)",
      "2. עודד פורר (שר החקלאות ופיתוח הנגב והגליל לשעבר)",
      "3. יבגני סובה (עיתונאי וסגן יו\"ר הכנסת)",
      "4. שרון ניר (תת-אלוף במיל' ויועצת הרמטכ\"ל לשעבר)",
      "5. יוליה מלינובסקי (עורכת דין ויו\"ר ועדת מיזמים מיוחדים)",
      "6. חמד עמאר (סגן שר האוצר לשעבר ונציג העדה הדרוזית)",
      "7. אלכס קושניר (יו\"ר ועדת הכספים לשעבר)",
      "8. בתיה כהנא-דרור (עו\"ד פמיניסטית דתית ופעילה ציבורית)",
      "9. פרופ' יוסי שיין (חוקר יחסים בינלאומיים)",
      "10. עו\"ד לימור מגן-תלם (משפטנית ונציגת הצעירים)"
    ],
    "platform": {
      "security": "קו ביטחוני תקיף ובלתי מתפשר, חיסול ראשי ארגוני הטרור, עונש מוות למחבלים, והצבת אולטימטום ברור מול חמאס, חיזבאללה ואיראן.",
      "economy": "כלכלה יצרנית וצומחת, עידוד יציאה לעבודה, שלילת קצבאות ממי שמסרב לעבוד, והורדת מיסים למעמד הביניים והעובדים.",
      "education": "חינוך ממלכתי איכותי, שלילת תקציבים ממוסד שלא מלמד 100% לימודי ליב\"ה ומדעים, והשקעה באקדמיה ובטכנולוגיה.",
      "enlistment": "חוק גיוס אחד לכולם בגיל 18: יהודי, מוסלמי, נוצרי, דרוזי, חרדי וחילוני – כולם משרתים בצה\"ל או בשירות אזרחי מלא ללא יוצא מן הכלל."
    }
  },
  {
    "id": "shas",
    "letter": "שס",
    "name": "התאחדות הספרדים שומרי תורה תנועת ש\"ס",
    "short": "ש״ס",
    "leader": "אריה דרעי",
    "color": "#2c3e50",
    "bloc": "right",
    "ballot_sub": "התאחדות הספרדים שומרי תורה תנועת ש\"ס",
    "surplus_partner": "gimel",
    "candidates": [
      "1. אריה מכלוף דרעי (יו\"ר תנועת ש\"ס)",
      "2. ינון אזולאי (חבר ועדת הכספים ומרכז סיעת ש\"ס)",
      "3. מיכאל מלכיאלי (השר לשירותי דת)",
      "4. יואב בן צור (שר העבודה)",
      "5. חיים ביטון (שר במשרד החינוך ומנכ\"ל תנועת ש\"ס)",
      "6. סא\"ל במיל' דרור עמוס (הממונה על המועצה הדתית בחיפה)",
      "7. משה אבוטבול (סגן שר החקלאות וראש עיריית בית שמש לשעבר)",
      "8. אוריאל בוסו (שר הבריאות)",
      "9. יוסף טייב (יו\"ר ועדת החינוך, התרבות והספורט)",
      "10. יונתן משריקי (יו\"ר ועדת הבריאות של הכנסת)"
    ],
    "platform": {
      "security": "עמדה ביטחונית נצית פרגמטית, שמירה על ביטחון ישראל ואזרחיה תוך התייעצות מתמדת עם מועצת חכמי התורה והדאגה לפריפריה.",
      "economy": "סוציאל-כלכלה מובהקת למען השכבות החלשות, כרטיסי מזון, סבסוד תחבורה ציבורית, מענקי חימום והעלאת קצבאות הבטחת הכנסה.",
      "education": "תקצוב שוויוני מלא לרשת החינוך 'בני יוסף' ולמוסדות התורניים, חיזוק מורשת יהדות ספרד והנחלת ערכי מסורת ויהדות.",
      "enlistment": "שמירה מוחלטת על מעמדם של לומדי התורה 'תורתם אומנותם', התנגדות נחרצת לסנקציות פליליות, ונכונות להסדרת מסלולים רק למי שאינו לומד."
    }
  },
  {
    "id": "emet",
    "letter": "אמת",
    "name": "הדמוקרטים בראשות יאיר גולן",
    "short": "הדמוקרטים",
    "leader": "יאיר גולן",
    "color": "#008850",
    "bloc": "center_left",
    "ballot_sub": "הדמוקרטים בראשות יאיר גולן",
    "surplus_partner": "ken",
    "candidates": [
      "1. יאיר גולן (יו\"ר המפלגה, אלוף במיל' וסגן הרמטכ\"ל לשעבר)",
      "2. נעמה לזימי (חברת כנסת ומובילת מאבקים חברתיים)",
      "3. גלעד קריב (עו\"ד, רב ויו\"ר ועדת החוקה לשעבר)",
      "4. אפרת רייטן מרום (עו\"ד ויו\"ר ועדת העבודה והרווחה לשעבר)",
      "5. יאיר פינק (מייסד 'לובי 99' וסגן אלוף במיל')",
      "6. גבריאלה לסקי שוץ (עורכת דין לזכויות אדם ונציגת מרצ)",
      "7. עמרי רונן (פעיל ציבור וממובילי המחאה האזרחית)",
      "8. מיכל רוזין (חברת כנסת לשעבר ומנכ\"לית מרצ)",
      "9. משה רדמן (יזם הייטק וממובילי המחאה האזרחית)",
      "10. סומייה בשיר (אשת חינוך, חברה ומנהיגות קהילתית)"
    ],
    "platform": {
      "security": "ביטחון מבוסס עוצמה צבאית וחתירה להסדר מדיני אזורי מתואם, סיום הסכסוך על בסיס שתי מדינות, ושיקום ההרתעה הדמוקרטית הישראלית.",
      "economy": "סוציאל-דמוקרטיה מתקדמת: חיזוק מדינת הרווחה, הגדלת שכר המינימום, פיקוח על מחירי מוצרי יסוד ודיור בר-השגה לכולם.",
      "education": "חינוך ציבורי שוויוני וחינמי מגיל לידה ועד תואר אקדמי, שלילת תקציבים ממוסדות שאינם מלמדים ליב\"ה ומדעים, וחינוך לשוויון זכויות.",
      "enlistment": "גיוס חובה שוויוני לכל חלקי החברה הישראלית, ביטול גורף של חוקי פטור לחרדים, הטלת סנקציות אישיות ומניעת קצבאות ממשתמטים."
    }
  },
  {
    "id": "bet",
    "letter": "ב",
    "name": "עוצמה יהודית בראשות איתמר בן גביר",
    "short": "עוצמה יהודית",
    "leader": "איתמר בן גביר",
    "color": "#c8102e",
    "bloc": "right",
    "ballot_sub": "עוצמה יהודית בראשות איתמר בן גביר",
    "surplus_partner": None,
    "candidates": [
      "1. איתמר בן גביר (יו\"ר המפלגה והשר לביטחון לאומי)",
      "2. יצחק שמעון וסרלאוף (שר הנגב, הגליל והחוסן הלאומי)",
      "3. אלמוג כהן (סגן שר וחבר כנסת, נציג הנגב)",
      "4. עמיחי אליהו (שר המורשת)",
      "5. תא\"ל במיל' צביקה פוגל (יו\"ר הוועדה לביטחון לאומי)",
      "6. לימור סון הר-מלך (חברת כנסת ופעילת התיישבות)",
      "7. יצחק קרויזר (יו\"ר סיעת עוצמה יהודית בכנסת)",
      "8. חנמאל שיראי דורפמן (ראש מטה השר לביטחון לאומי ועו\"ד)",
      "9. צחי יצחק אליהו (איש ציבור ומנהל מוסדות)",
      "10. יוסף יצחק גולדברגר (נציג קהילות ירושלים ופעיל ימין)"
    ],
    "platform": {
      "security": "עונש מוות למחבלים, גירוש תומכי טרור, חופש פעולה מלא ללוחמים ושוטרים, הקמת משמר לאומי עוצמתי והשבת הריבונות והביטחון האישי.",
      "economy": "הורדת מיסים, תמיכה בעסקים בנגב ובגליל, מתן עדיפות כלכלית ומענקים מוגדלים ללוחמים ולמשוחררי צה\"ל.",
      "education": "חיזוק תכני זהות יהודית, ציונות וערכי לחימה בבתי הספר, והסרת תכנים פרוגרסיביים ממערכת החינוך.",
      "enlistment": "שירות צבאי כחובה לאומית לכל יהודי תוך התאמת תנאים לחרדים, החמרת תנאי האסירים הביטחוניים, וביטול כל פטור למי שמסית נגד המדינה."
    }
  },
  {
    "id": "gimel",
    "letter": "ג",
    "name": "יהדות התורה והשבת אגודת ישראל – דגל התורה",
    "short": "יהדות התורה",
    "leader": "יעקב אשר ויצחק גולדקנופף",
    "color": "#34495e",
    "bloc": "right",
    "ballot_sub": "יהדות התורה והשבת אגודת ישראל – דגל התורה",
    "surplus_partner": "shas",
    "candidates": [
      "1. יעקב אשר (יו\"ר ועדת הפנים והגנת הסביבה, דגל התורה)",
      "2. יצחק יששכר גולדקנופף (שר הבינוי והשיכון, אגודת ישראל)",
      "3. יצחק זאב פינדרוס (יו\"ר סיעת יהדות התורה בכנסת, דגל התורה)",
      "4. מאיר פרוש (שר ירושלים ומסורת ישראל, חומת תורת ישראל)",
      "5. משה עזריאל רוזנטל (איש ציבור מוביל, דגל התורה)",
      "6. אלי שטארק (נציג חומת תורת ישראל)",
      "7. יהודה לייב וויספיש (מנהל מוסדות תורה, דגל התורה)",
      "8. יואל יעקב טסלר (סגן שר התרבות והספורט, אגודת ישראל)",
      "9. דוד זלץ (איש עשייה מוניציפלי, דגל התורה)",
      "10. דוד אוחנה (נציג הקהילות החרדיות, דגל התורה)"
    ],
    "platform": {
      "security": "התמקדות בביטחון העם היהודי בארצו על פי הדרכת גדולי ישראל, שמירה על הסטטוס קוו הדתי והימנעות מעימותים בינלאומיים מיותרים.",
      "economy": "תקציבים לעולם הישיבות, פתרונות דיור מוזלים בריכוזים חרדיים, סבסוד מעונות יום ותמיכה במשפחות ברוכות ילדים.",
      "education": "אוטונומיה חינוכית מלאה למוסדות החינוך החרדי ללא התערבות בתכני הלימוד, והשוואת תקציבי תלמיד ישיבה לתלמיד במערכת הכללית.",
      "enlistment": "לימוד התורה הוא ערך עליון המגן על עם ישראל; דרישה לעיגון חוקי פטור מלא לכל בחור ישיבה שלומד, ודחייה מוחלטת של יעדי גיוס כפויים."
    }
  },
  {
    "id": "tet",
    "letter": "ט",
    "name": "הציונות הדתית בראשות בצלאל סמוטריץ' וזהות בראשות משה פייגלין",
    "short": "הציונות הדתית וזהות",
    "leader": "בצלאל סמוטריץ' ומשה פייגלין",
    "color": "#e87722",
    "bloc": "right",
    "ballot_sub": "הציונות הדתית בראשות בצלאל סמוטריץ' וזהות בראשות משה פייגלין",
    "surplus_partner": "mahal",
    "candidates": [
      "1. בצלאל יואל סמוטריץ' (שר האוצר ושר במשרד הביטחון)",
      "2. משה זלמן פייגלין (יו\"ר תנועת זהות וסגן יו\"ר הכנסת לשעבר)",
      "3. אורית מלכה סטרוק (שרת ההתיישבות והמשימות הלאומיות)",
      "4. שמחה דן רוטמן (יו\"ר ועדת החוקה, חוק ומשפט)",
      "5. צבי מור (ממובילי פורום תקווה ואיש חינוך)",
      "6. איתמר מרדכי איתם (סגן אלוף במיל' ואיש התיישבות)",
      "7. צבי ידידיה סוכות (חבר כנסת ויו\"ר ועדת המשנה ליו\"ש)",
      "8. יצחק חי זאגא (איש הגות ומשפטן, תנועת זהות)",
      "9. רעות בן חיים (ממובילות תנועת 'צו 9' ופעילה חברתית)",
      "10. עומר פציניאש וולדמן (נציג הדור הצעיר ופעיל זהות)"
    ],
    "platform": {
      "security": "החלת ריבונות ישראלית מלאה על כל יהודה, שומרון ועזה, שלילת כל רעיון של מדינה פלסטינית, הכרעה צבאית טוטאלית ועידוד הגירה מרצון.",
      "economy": "שוק חופשי מוחלט, ביטול מונופולים ממשלתיים, הפרטת חברות ממשלתיות, הפחתת מסים וצמצום כוחם של ועדי העובדים הגדולים.",
      "education": "חיזוק החינוך הדתי-לאומי והתורני, העמקת לימודי תנ\"ך ומורשת יהודית, והטמעת גאווה לאומית בכל שכבות הגיל.",
      "enlistment": "הצדעה לחיילי הציונות הדתית ולמילואימניקים המשרתים בחזית, קידום מסגרות מותאמות לשילוב חרדים, והגנה על לימוד התורה כמגן רוחני של העם."
    }
  },
  {
    "id": "vdm",
    "letter": "ודעם",
    "name": "הרשימה המשותפת (חד\"ש, תע\"ל, בל\"ד) בראשות יוסף ג'בארין ואחמד טיבי",
    "short": "הרשימה המשותפת",
    "leader": "יוסף ג'בארין ואחמד טיבי",
    "color": "#d9232a",
    "bloc": "arab",
    "ballot_sub": "הרשימה המשותפת (חד\"ש, תע\"ל, בל\"ד)",
    "surplus_partner": None,
    "candidates": [
      "1. ד\"ר יוסף ג'בארין (יו\"ר חד\"ש, מרצה למשפטים וחבר כנסת לשעבר)",
      "2. ד\"ר אחמד טיבי (יו\"ר תע\"ל וסגן יו\"ר הכנסת)",
      "3. סאמי אבו שחאדה (יו\"ר בל\"ד וחבר כנסת לשעבר)",
      "4. ד\"ר פאתן גטאס (איש אקדמיה ופעיל חד\"ש)",
      "5. בכר עואודה (מנכ\"ל עמותת הגליל ופעיל בל\"ד)",
      "6. ד\"ר עופר כסיף (מרצה למדע המדינה וחבר כנסת, חד\"ש)",
      "7. יוסף עטאונה (נציג הנגב והחברה הבדואית, חד\"ש)",
      "8. ד\"ר מהא כרכבי־סבאח (סוציולוגית וחוקרת, בל\"ד)",
      "9. עו\"ד אחמד דראושה (משפטן ואיש ציבור, תע\"ל)",
      "10. ד\"ר נהאיה ושאחי (אשת חינוך ורווחה, חד\"ש)"
    ],
    "platform": {
      "security": "סיום מיידי של המלחמה והכיבוש, הקמת מדינה פלסטינית עצמאית שבירתה מזרח ירושלים, פירוק ההתנחלויות וחתירה לשלום צודק.",
      "economy": "צדק חלוקתי וכלכלה סוציאליסטית: מיסוי עשירים ותאגידים, הגנה על זכויות עובדים, והשוואת תשתיות מלאה ליישובים הערביים.",
      "education": "חינוך שוויוני, ביטול אפליה בתקציבים, חיזוק החינוך לדו-קיום, דמוקרטיה וזכויות אדם, ופיתוח תוכניות לימוד בערבית.",
      "enlistment": "התנגדות מוחלטת לכל סוגי הגיוס לצבא או לשירות לאומי-אזרחי ככלי לשליטה, ומאבק לזכויות אזרחיות מלאות ללא תלות בשירות."
    }
  },
  {
    "id": "am",
    "letter": "עם",
    "name": "רע\"ם - הרשימה הערבית המאוחדת",
    "short": "רע\"ם",
    "leader": "מנסור עבאס",
    "color": "#007a3d",
    "bloc": "arab",
    "ballot_sub": "רע\"ם - הרשימה הערבית המאוחדת",
    "surplus_partner": None,
    "candidates": [
      "1. ד\"ר מנסור עבאס (יו\"ר רע\"ם וסגן יו\"ר הכנסת לשעבר)",
      "2. וליד טאהא (יו\"ר ועדת הפנים לשעבר)",
      "3. ווליד אל-הואשלה (נציג הנגב והתנועה האסלאמית)",
      "4. אימאן ח'טיב-יאסין (עובדת סוציאלית והאישה הראשונה מחבושת חיג'אב בכנסת)",
      "5. ד\"ר יאסר חוג'יראת (רופא ומנהל מחלקה)",
      "6. עבד אל-כרים ג'מאל (מהנדס ואיש ציבור)",
      "7. עלאא דיאב (פעיל חברתי וקהילתי)",
      "8. ח'אלד דראושה (איש חינוך ורווחה)",
      "9. איברהים אל-עוקבי (נציג הכפרים הבלתי מוכרים)",
      "10. עטא אבו מדיעם (ראש עיריית רהט לשעבר)"
    ],
    "platform": {
      "security": "סיום הכיבוש והקמת מדינה פלסטינית לצד ישראל, חתירה לשלום צודק וכולל, והתמקדות בהשגת ביטחון פנים ומיגור הפשיעה בחברה הערבית.",
      "economy": "פיתוח כלכלי אזרחי לחברה הערבית, הקצאת תקציבי תוכניות החומש, הרחבת אזורי תעשייה ופתרונות תעסוקה לאקדמאים ערבים.",
      "education": "שדרוג בתי הספר הערביים, חיזוק החינוך הטכנולוגי והמדעי, פתרון מצוקת הכיתות, ושימור השפה והזהות התרבותית הערבית.",
      "enlistment": "התנגדות עקרונית לגיוס צעירים ערבים לצה\"ל, תמיכה בשירות אזרחי התנדבותי בתוך היישובים הערביים בלבד לרווחת הקהילה."
    }
  },
  {
    "id": "derech",
    "letter": "דרך",
    "name": "ישר! בראשות גדי איזנקוט",
    "short": "ישר",
    "leader": "גדי איזנקוט",
    "color": "#4f46e5",
    "bloc": "center_left",
    "ballot_sub": "ישר! בראשות גדי איזנקוט",
    "surplus_partner": "rak",
    "candidates": [
      "1. גדי איזנקוט (יו\"ר המפלגה, רא\"ל במיל' ורמטכ\"ל לשעבר)",
      "2. יורם כהן (ראש שירות הביטחון הכללי - שב\"כ לשעבר)",
      "3. אורית פרקש הכהן (שרת המדע, התיירות והתשתיות לשעבר)",
      "4. עדי אלטשולר (יזמת חברתית, מייסדת 'כנפיים של קרמבו' ו'זיכרון בסלון')",
      "5. מתן כהנא (סגן שר הדתות ולוחם סיירת מטכ\"ל לשעבר)",
      "6. חילי טרופר (שר התרבות והספורט לשעבר ואיש חינוך)",
      "7. שאול מרידור (ראש אגף התקציבים במשרד האוצר לשעבר)",
      "8. תאיר איפרגן (מנכ\"לית משרד הכלכלה והתעשייה לשעבר)",
      "9. אושרת גני גונן (ראשת המועצה האזורית דרום השרון)",
      "10. שירה שפירא (מנהלת ואשת חינוך)"
    ],
    "platform": {
      "security": "תפיסת ביטחון לאומי מעודכנת, סדר עדיפויות אסטרטגי ברור, שיקום האמון בפיקוד הצבאי, והסדרה מדינית עם בנות הברית במזרח התיכון.",
      "economy": "תקציב ביטחון אחראי ומבוקר, הסטת משאבים לצמיחה אזרחית, מאבק בריכוזיות במשק והקלה דרמטית ביוקר הדיור והמחיה.",
      "education": "חינוך לדמוקרטיה, שלטון החוק ואזרחות פעילה, סגירת פערים בין מרכז לפריפריה, והבטחת השכלה איכותית לכל תלמיד.",
      "enlistment": "חובת גיוס ברורה ומוחלטת לכל אזרח יהודי: צה\"ל הוא צבא העם, אין מקום לאפליית דם, ועמידה על יעדי גיוס שנתיים קשיחים עם סנקציות."
    }
  },
  {
    "id": "kach",
    "letter": "ך",
    "name": "עמך ישראל בראשות עופר וינטר",
    "short": "עמך ישראל",
    "leader": "עופר וינטר",
    "color": "#15803d",
    "bloc": "new",
    "is_new": True,
    "ballot_sub": "עמך ישראל בראשות עופר וינטר",
    "surplus_partner": None,
    "candidates": [
      "1. תא\"ל במיל' עופר וינטר (יו\"ר המפלגה, מפקד חטיבת גבעתי ועוצבת האש לשעבר)",
      "2. יוסף חדאד (פעיל הסברה ישראלי מוביל)",
      "3. נטעלי שם טוב (עיתונאית ומגישת חדשות)",
      "4. אל\"מ במיל' ערן בן-ארי (משפטן וקצין מילואים)",
      "5. פלר חסן-נחום (משנה לראש עיריית ירושלים לשעבר ושגרירה מיוחדת)",
      "6. ללי דרעי (פעילה חברתית ואם שכולה)",
      "7. רונן בודנרו (איש עסקים ויזם)",
      "8. דוידי בן ציון (סגן ראש מועצת שומרון ורס\"ן במיל')",
      "9. אביב עזרא (דיפלומט ושגריר ישראל לשעבר)",
      "10. סיגל קראוניק-עטיה (אלמנתו של רבש\"ץ קיבוץ חולית)"
    ],
    "platform": {
      "security": "הכרעה, תעוזה ורוח לחימה יהודית, חתירה למגע וניצחון ללא גמגום, שינוי הוראות פתיחה באש ומתן גיבוי מלא ללוחמים בשטח.",
      "economy": "דאגה לאזרח הפשוט ולפריפריה, פיתוח יישובי הספר וההתיישבות, והקלות כלכליות לחיילים ולמשפחות המילואים.",
      "education": "חינוך לגבורה, לאהבת העם והארץ, חיבור עמוק לשורשים ולתנ\"ך לצד מצוינות אישית ומנהיגות.",
      "enlistment": "עידוד גיוס משמעותי מכל חלקי העם, יצירת מסלולי לחימה מותאמים לחרדים תוך שמירה מלאה על אורח חייהם ואמונתם."
    }
  },
  {
    "id": "day",
    "letter": "די",
    "name": "המילואימניקים והכלכלית בראשות יועז הנדל וירון זליכה",
    "short": "המילואימניקים",
    "leader": "יועז הנדל וירון זליכה",
    "color": "#0d9488",
    "bloc": "new",
    "is_new": True,
    "ballot_sub": "המילואימניקים והכלכלית בראשות יועז הנדל וירון זליכה",
    "surplus_partner": "lamed",
    "candidates": [
      "1. יועז הנדל (יו\"ר המפלגה, שר התקשורת לשעבר ולוחם שייטת 13)",
      "2. פרופ' ירון זליכה (ראש המפלגה הכלכלית והחשב הכללי לשעבר באוצר)",
      "3. ד\"ר עינת וילף (חברת כנסת לשעבר וסופרת)",
      "4. חביב ווליבוביץ (איש כלכלה ויזם עסקי)",
      "5. יואב שלמה אדומי (לוחם מילואים ואיש ציבור)",
      "6. אופיר שי לנגמן (מומחה פיננסים וניהול)",
      "7. שלומי דמרי (ממובילי מטה המילואימניקים)",
      "8. ליאור גלבוע (פעיל חברתי וכלכלי)",
      "9. תהילה פרץ (מובילת מאבקי משפחות המילואימניקים)",
      "10. שלום ביטון (איש ניהול וקהילה)"
    ],
    "platform": {
      "security": "יד ברזל ביטחונית, הכרעת אויבי ישראל, הגדלת סדר הכוחות של צה\"ל ב-30%, ומתן עדיפות לאומית ראשונה ללוחמי המילואים.",
      "economy": "מלחמה חסרת פשרות במונופולים וביבואנים הבלעדיים, פירוק קרטלים, הורדת מע\"מ על מזון ותרופות, ומענקים משמעותיים למשרתים.",
      "education": "חינוך ממלכתי איכותי, הטמעת לימודי ליב\"ה ומדעים בכל בתי הספר ללא פשרות, והקניית מיומנויות טכנולוגיות וכלכליות.",
      "enlistment": "חובת שירות קרבי או לאומי שוויוני לכולם; ביטול מוחלט של קומבינות הפטור, והתניית זכויות והטבות מדינה בביצוע שירות פעיל."
    }
  },
  {
    "id": "blank",
    "letter": "פתק לבן",
    "name": "פתק לבן (הצבעת מחאה / קול פסול)",
    "short": "פתק לבן",
    "leader": "ללא מנהיג",
    "color": "#9ca3af",
    "bloc": "invalid",
    "ballot_sub": "פתק לבן ריק - ללא אותיות וללא כינוי",
    "surplus_partner": None,
    "candidates": [
      "פתק הצבעה לבן וריק לחלוטין",
      "משמש להבעת מחאה אזרחית בקלפי",
      "על פי חוק הבחירות, נספר כקול פסול ואינו מחלק מנדטים"
    ],
    "platform": {
      "security": "הצבעת מחאה: אי-אמון במערכת הביטחונית או בפתרונות המוצעים על ידי המפלגות הקיימות.",
      "economy": "הבעת ייאוש מיוקר המחיה ומהבטחות כלכליות של נבחרי הציבור שאינן ממומשות.",
      "education": "קריאה לרה-ארגון יסודי של סדרי העדיפויות הלאומיים ומערכת הממשל בישראל.",
      "enlistment": "פתק לבן אינו נספר בחלוקת המנדטים ונחשב כקול פסול על פי חוק הבחירות לכנסת."
    }
  }
]


_firebase_credential_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")
_firebase_database_url = os.environ.get("FIREBASE_DATABASE_URL")

if not _firebase_credential_json or not _firebase_database_url:
    raise RuntimeError(
        "Firebase is not configured. Set FIREBASE_DATABASE_URL and "
        "FIREBASE_SERVICE_ACCOUNT_JSON; refusing to fall back to local file storage."
    )

firebase_admin.initialize_app(
    credentials.Certificate(json.loads(_firebase_credential_json)),
    {"databaseURL": _firebase_database_url.rstrip("/")}
)
FIREBASE_ROOT = firebase_db.reference("election_data")


def _empty_data():
    return {
        "voted_devices": {},
        "voted_ips": {},
        "votes": {p["id"]: 0 for p in PARTIES},
        "reset_id": int(datetime.now().timestamp())
    }

def load_data():
    data = FIREBASE_ROOT.get()
    if not isinstance(data, dict):
        data = _empty_data()
        FIREBASE_ROOT.set(data)
    data.setdefault("voted_devices", {})
    data.setdefault("voted_ips", {})
    data.setdefault("votes", {})
    for p in PARTIES:
        data["votes"].setdefault(p["id"], 0)
    data.setdefault("reset_id", 0)
    return data

def save_data(data):
    forbidden = set(".$#[]/")

    def find_invalid_keys(obj, path="$"):
        problems = []

        if isinstance(obj, dict):
            for key, value in obj.items():
                if (
                    not isinstance(key, str)
                    or not key
                    or any(char in key for char in forbidden)
                ):
                    # לא מדפיסים את תוכן המפתח, כדי לא לחשוף פרטים אישיים
                    problems.append(path)

                problems.extend(find_invalid_keys(value, path + "/..."))

        elif isinstance(obj, list):
            for value in obj:
                problems.extend(find_invalid_keys(value, path + "/[]"))

        return problems

    problems = find_invalid_keys(data)

    if problems:
        raise ValueError(
            f"Invalid Firebase key detected at: {', '.join(problems)}"
        )

    FIREBASE_ROOT.set(data)
class ThreadingElectionServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    daemon_threads = True
    allow_reuse_address = True

class ElectionHandler(http.server.SimpleHTTPRequestHandler):
    def get_client_ip(self):
        xfwd = self.headers.get("X-Forwarded-For")
        if xfwd:
            return xfwd.split(",")[0].strip()
        return self.client_address[0]

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Voter-Device-Id")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Voter-Device-Id")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path in ["/", "/index.html", "/vote"]:
            html_p = HTML_FILE if os.path.exists(HTML_FILE) else os.path.join(os.path.dirname(__file__), HTML_FILE)
            if os.path.exists(html_p):
                with open(html_p, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
                self.end_headers()
                self.wfile.write(content)
                return

        if path == "/api/ip":
            ip = self.get_client_ip()
            with db_lock:
                data = load_data()
                voted = ip in data.get("voted_ips", {})
            self.send_json({"ip": ip, "has_voted": voted})
            return

        if path == "/api/parties":
            self.send_json(PARTIES)
            return

        if path == "/api/results":
            with db_lock:
                data = load_data()
                votes = data.get("votes", {})
                voted_devices = data.get("voted_devices", {})
                total_votes = sum(votes.values())
                voted_cnt = len(voted_devices)
                res = {
                    "success": True,
                    "votes": votes,
                    "total_votes": total_votes,
                    "voted_count": voted_cnt,
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                }
            self.send_json(res)
            return

        super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(length) if length > 0 else b"{}"

        try:
            payload = json.loads(post_data.decode("utf-8")) if post_data else {}
        except Exception:
            payload = {}

        if path == "/api/vote":
            client_ip = self.get_client_ip()
            party_id = payload.get("party_id")
            device_id = payload.get("voter_device_id") or self.headers.get("X-Voter-Device-Id") or client_ip
          print("VOTE DEBUG:", {     "party_id_present": bool(party_id),     "party_id_valid": any(p["id"] == party_id for p in PARTIES),     "device_id_type": type(device_id).__name__,     "device_id_length": len(device_id) if isinstance(device_id, str) else None,     "client_ip_valid": isinstance(client_ip, str) and bool(client_ip) })
print("VOTE DEBUG:", {
    "party_id_present": bool(party_id),
    "party_id_valid": any(p["id"] == party_id for p in PARTIES),
    "device_id_type": type(device_id).__name__,
    "device_id_length": len(device_id) if isinstance(device_id, str) else None,
    "client_ip_valid": isinstance(client_ip, str) and bool(client_ip)
})
            if not party_id:
                self.send_json({"error": "נא לספק מזהה מפלגה"}, 400)
                return

            valid = next((p for p in PARTIES if p["id"] == party_id), None)
            if not valid:
                self.send_json({"error": "מפלגה לא חוקית"}, 400)
                return

            with db_lock:
                data = load_data()
                voted_devs = data.setdefault("voted_devices", {})
                voted_ips = data.setdefault("voted_ips", {})

                # אכיפת הצבעה אחת למכשיר (מאפשר למאות מכשירים שונים ברשת/Wi-Fi להצביע במקביל!)
                if device_id in voted_devs:
                    self.send_json({
                        "error": "מכשיר זה כבר ביצע הצבעה במערכת זו.",
                        "already_voted": True,
                        "votes": data["votes"],
                        "total_votes": sum(data["votes"].values()),
                        "voted_count": len(voted_devs)
                    }, 403)
                    return

                for label, key in (
                    ("device_id", device_id),
                    ("client_ip", client_ip),
                ):
                    if (
                        not isinstance(key, str)
                        or not key
                        or any(char in key for char in ".$#[]/")
                    ):
                      print(f"Invalid Firebase key: {label}")
                      print(f"Invalid Firebase key: {label}; type={type(key).__name__}; length={len(key) if isinstance(key, str) else 'N/A'}; invalid_chars={[c for c in key if c in '.$#[]/'] if isinstance(key, str) else 'N/A'}")
                        self.send_json(
                            {"error": "מזהה המצביע אינו תקין. יש לנסות שוב."},
                            400
                        )
                        return

                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
              
                voted_devs[device_id] = {
                    "party_id": party_id,
                    "party_letter": valid["letter"],
                    "party_name": valid["name"],
                    "ip": client_ip,
                    "timestamp": now
                }
                voted_ips[client_ip] = {
                    "party_id": party_id,
                    "timestamp": now
                }
                data.setdefault("votes", {})[party_id] = data.get("votes", {}).get(party_id, 0) + 1
                save_data(data)

                total_v = sum(data["votes"].values())
                voted_cnt = len(voted_devs)
                updated_votes = dict(data["votes"])

            self.send_json({
                "success": True,
                "votes": updated_votes,
                "total_votes": total_v,
                "voted_count": voted_cnt,
                "party": valid["name"],
                "letter": valid["letter"]
            })
            return

        if path == "/api/admin/verify_pin":
            pin = str(payload.get("pin", "")).strip()
            is_valid = (pin in ["2026", "1234"])
            self.send_json({"valid": is_valid})
            return

        if path == "/api/admin/reset":
            pin = str(payload.get("pin", "")).strip()
            if pin not in ["2026", "1234"]:
                self.send_json({"error": "קוד גישה שגוי"}, 401)
                return
            with db_lock:
                data = {
                    "voted_devices": {},
                    "voted_ips": {},
                    "votes": {p["id"]: 0 for p in PARTIES}
                }
                save_data(data)
                res_votes = dict(data["votes"])
            self.send_json({"success": True, "votes": res_votes, "total_votes": 0, "voted_count": 0})
            return

        if path == "/api/admin/inject":
            pin = str(payload.get("pin", "")).strip()
            if pin not in ["2026", "1234"]:
                self.send_json({"error": "קוד גישה שגוי"}, 401)
                return
            sample_weights = {
                "mahal": 2600,
                "rak": 2300,
                "ken": 1300,
                "lamed": 1100,
                "shas": 1000,
                "emet": 900,
                "bet": 800,
                "gimel": 800,
                "tet": 500,
                "vdm": 500,
                "am": 500,
                "derech": 400,
                "kach": 400,
                "day": 400,
                "blank": 120,
            }
            with db_lock:
                data = load_data()
                for pid, cnt in sample_weights.items():
                    data.setdefault("votes", {})[pid] = data.get("votes", {}).get(pid, 0) + cnt
                save_data(data)
                res_votes = dict(data["votes"])
                tot_v = sum(res_votes.values())
                cnt_dev = len(data.get("voted_devices", {})) + 10000
            self.send_json({"success": True, "votes": res_votes, "total_votes": tot_v, "voted_count": cnt_dev})
            return

        self.send_json({"error": "Not found"}, 404)

if __name__ == "__main__":
    load_data()
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    try:
        with ThreadingElectionServer(("", port), ElectionHandler) as httpd:
            print(f"\n✓ שרת הבחירות (גרסה 4.0 רב-מכשיר סימולטני) פועל בכתובת: http://localhost:{port}")
            print(f"לתמיכה בריבוי מכשירים וסנכרון חי, השרת מאפשר למאות מכשירים להצביע במקביל.")
            print(f"לעצירת השרת: Ctrl + C\n")
            httpd.serve_forever()
    except OSError as e:
        if e.errno == 98:
            print(f"\n⚠️ פורט {port} כבר תפוס על ידי שרת שרץ ברקע!")
            print(f"👉 לשחרור הפורט הרץ:  fuser -k {port}/tcp  או  pkill -f election_server.py")
            print(f"👉 או הרץ על פורט אחר:  python3 election_server.py {port+1}\n")
        sys.exit(1)
