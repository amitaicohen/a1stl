#!/usr/bin/env python3
"""
שרת בחירות 2026 לכנסת ה-26 (27 באוקטובר 2026)
Python HTTP & REST API Server (Built-in standard library).
"""

import http.server
import socketserver
import urllib.parse
import json
import os
import sys
from datetime import datetime

PORT = 8000
DATA_FILE = "elections_data.json"
HTML_FILE = "israel_elections_app.html"

PARTIES = [
  {
    "id": "mahal",
    "letter": "מחל",
    "name": "הליכוד בהנהגת בנימין נתניהו לראשות הממשלה",
    "short": "הליכוד",
    "leader": "בנימין נתניהו",
    "color": "#1877f2",
    "bloc": "right",
    "ballot_sub": "הליכוד בהנהגת בנימין נתניהו לראשות הממשלה"
  },
  {
    "id": "po",
    "letter": "פה",
    "name": "יש עתיד בראשות יאיר לפיד",
    "short": "יש עתיד",
    "leader": "יאיר לפיד",
    "color": "#00a3e0",
    "bloc": "center_left",
    "ballot_sub": "יש עתיד בראשות יאיר לפיד"
  },
  {
    "id": "ken",
    "letter": "כן",
    "name": "כחול לבן המחנה הממלכתי בהנהגת בני גנץ",
    "short": "המחנה הממלכתי",
    "leader": "בני גנץ",
    "color": "#002b49",
    "bloc": "center_left",
    "ballot_sub": "כחול לבן המחנה הממלכתי בהנהגת בני גנץ"
  },
  {
    "id": "rak",
    "letter": "רק",
    "name": "ביחד בראשות נפתלי בנט",
    "short": "ביחד",
    "leader": "נפתלי בנט",
    "color": "#2563eb",
    "bloc": "center_left",
    "ballot_sub": "ביחד בראשות נפתלי בנט"
  },
  {
    "id": "derech",
    "letter": "דרך",
    "name": "ישר בראשות גדי איזנקוט",
    "short": "ישר",
    "leader": "גדי איזנקוט",
    "color": "#4f46e5",
    "bloc": "center_left",
    "ballot_sub": "ישר בראשות גדי איזנקוט"
  },
  {
    "id": "emet",
    "letter": "אמת",
    "name": "הדמוקרטים בראשות יאיר גולן",
    "short": "הדמוקרטים",
    "leader": "יאיר גולן",
    "color": "#008850",
    "bloc": "center_left",
    "ballot_sub": "הדמוקרטים בראשות יאיר גולן"
  },
  {
    "id": "tet",
    "letter": "ט",
    "name": "מפלגת הציונות הדתית וזהות בראשות בצלאל סמוטריץ' ומשה פייגלין",
    "short": "הציונות הדתית וזהות",
    "leader": "בצלאל סמוטריץ' ומשה פייגלין",
    "color": "#e87722",
    "bloc": "right",
    "ballot_sub": "מפלגת הציונות הדתית וזהות בראשות סמוטריץ' ופייגלין"
  },
  {
    "id": "bet",
    "letter": "ב",
    "name": "עוצמה יהודית בראשות איתמר בן גביר",
    "short": "עוצמה יהודית",
    "leader": "איתמר בן גביר",
    "color": "#c8102e",
    "bloc": "right",
    "ballot_sub": "עוצמה יהודית בראשות איתמר בן גביר"
  },
  {
    "id": "shas",
    "letter": "שס",
    "name": "התאחדות הספרדים שומרי תורה תנועת ש\"ס",
    "short": "ש\"ס",
    "leader": "אריה דרעי",
    "color": "#2c3e50",
    "bloc": "right",
    "ballot_sub": "התאחדות הספרדים שומרי תורה תנועת ש\"ס"
  },
  {
    "id": "gimel",
    "letter": "ג",
    "name": "יהדות התורה והשבת אגודת ישראל - דגל התורה",
    "short": "יהדות התורה",
    "leader": "יצחק גולדקנופף ומשה גפני",
    "color": "#34495e",
    "bloc": "right",
    "ballot_sub": "יהדות התורה והשבת אגודת ישראל - דגל התורה"
  },
  {
    "id": "lamed",
    "letter": "ל",
    "name": "ישראל ביתנו בראשות אביגדור ליברמן",
    "short": "ישראל ביתנו",
    "leader": "אביגדור ליברמן",
    "color": "#005596",
    "bloc": "right",
    "ballot_sub": "ישראל ביתנו בראשות אביגדור ליברמן"
  },
  {
    "id": "am",
    "letter": "עם",
    "name": "רע\"ם - הרשימה הערבית המאוחדת",
    "short": "רע\"ם",
    "leader": "מנסור עבאס",
    "color": "#007a3d",
    "bloc": "arab",
    "ballot_sub": "רע\"ם - הרשימה הערבית המאוחדת"
  },
  {
    "id": "vdm",
    "letter": "ודם",
    "name": "חד\"ש - תע\"ל בראשות איימן עודה ואחמד טיבי",
    "short": "חד\"ש-תע\"ל",
    "leader": "איימן עודה ואחמד טיבי",
    "color": "#d9232a",
    "bloc": "arab",
    "ballot_sub": "חד\"ש - תע\"ל בראשות איימן עודה ואחמד טיבי"
  },
  {
    "id": "dalet",
    "letter": "ד",
    "name": "בל\"ד - אלתג'מוע אלדמוקרטי",
    "short": "בל\"ד",
    "leader": "סאמי אבו שחאדה",
    "color": "#f58220",
    "bloc": "arab",
    "ballot_sub": "בל\"ד - אלתג'מוע אלדמוקרטי"
  },
  {
    "id": "ni",
    "letter": "ני",
    "name": "מפלגת נעם לישראל בראשות אבי מעוז",
    "short": "נעם",
    "leader": "אבי מעוז",
    "color": "#854d0e",
    "bloc": "right",
    "ballot_sub": "נעם לישראל בראשות אבי מעוז"
  },
  {
    "id": "day",
    "letter": "די",
    "name": "המילואימניקים והכלכלית בראשות יועז הנדל וירון זליכה",
    "short": "המילואימניקים",
    "leader": "יועז הנדל וירון זליכה",
    "color": "#0d9488",
    "bloc": "other",
    "ballot_sub": "המילואימניקים והכלכלית בראשות יועז הנדל וירון זליכה"
  },
  {
    "id": "kach",
    "letter": "ך",
    "name": "עמך ישראל בראשות עופר וינטר",
    "short": "עמך ישראל",
    "leader": "עופר וינטר",
    "color": "#15803d",
    "bloc": "right",
    "ballot_sub": "עמך ישראל בראשות עופר וינטר"
  },
  {
    "id": "yod",
    "letter": "י",
    "name": "ישראל תחילה בראשות שרן השכל",
    "short": "ישראל תחילה",
    "leader": "שרן השכל",
    "color": "#7e22ce",
    "bloc": "other",
    "ballot_sub": "ישראל תחילה בראשות שרן השכל"
  },
  {
    "id": "hei",
    "letter": "ה",
    "name": "גן עדן בראשות ישוע ישראל בן דוד",
    "short": "גן עדן",
    "leader": "ישוע ישראל בן דוד",
    "color": "#14b8a6",
    "bloc": "other",
    "ballot_sub": "גן עדן בראשות ישוע ישראל בן דוד"
  },
  {
    "id": "zach",
    "letter": "זך",
    "name": "צעירים בוערים",
    "short": "צעירים בוערים",
    "leader": "הדר מוכתר",
    "color": "#ea580c",
    "bloc": "other",
    "ballot_sub": "צעירים בוערים"
  },
  {
    "id": "blank",
    "letter": "פתק לבן",
    "name": "פתק לבן (הצבעת מחאה / קול פסול)",
    "short": "פתק לבן",
    "leader": "קול פסול",
    "color": "#9ca3af",
    "bloc": "invalid",
    "ballot_sub": "פתק לבן ריק - ללא אותיות"
  }
]

def load_data():
    if not os.path.exists(DATA_FILE):
        initial = {
            "voted_ips": {},
            "votes": {p["id"]: 0 for p in PARTIES}
        }
        save_data(initial)
        return initial
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        initial = {
            "voted_ips": {},
            "votes": {p["id"]: 0 for p in PARTIES}
        }
        save_data(initial)
        return initial

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def calculate_bader_ofer():
    data = load_data()
    votes = data.get("votes", {})
    total_ballots = sum(votes.values())
    blank_votes = votes.get("blank", 0)
    valid_votes = total_ballots - blank_votes

    threshold_pct = 3.25
    threshold_votes = (valid_votes * threshold_pct / 100.0) if valid_votes > 0 else 0

    qualifying = []
    non_qualifying = []

    for p in PARTIES:
        p_id = p["id"]
        count = votes.get(p_id, 0)
        pct = (count / valid_votes * 100.0) if valid_votes > 0 else 0.0
        is_blank = (p_id == "blank")
        passed = (not is_blank and valid_votes > 0 and count >= threshold_votes)

        entry = {
            "id": p_id,
            "letter": p["letter"],
            "name": p["name"],
            "short": p["short"],
            "color": p["color"],
            "votes": count,
            "pct": round(pct, 2),
            "passed": passed,
            "seats": 0
        }
        if passed:
            qualifying.append(entry)
        else:
            non_qualifying.append(entry)

    TOTAL_SEATS = 120
    if qualifying and valid_votes > 0:
        qual_votes_sum = sum(p["votes"] for p in qualifying)
        quota = qual_votes_sum / TOTAL_SEATS
        allocated = 0
        for p in qualifying:
            p["seats"] = int(p["votes"] // quota)
            allocated += p["seats"]

        remaining = TOTAL_SEATS - allocated
        for _ in range(remaining):
            best = None
            best_q = -1
            for p in qualifying:
                q = p["votes"] / (p["seats"] + 1)
                if q > best_q:
                    best_q = q
                    best = p
            if best:
                best["seats"] += 1

    all_results = sorted(qualifying + non_qualifying, key=lambda x: (x["seats"], x["votes"]), reverse=True)
    return {
        "total_ballots": total_ballots,
        "valid_votes": valid_votes,
        "blank_votes": blank_votes,
        "threshold_votes": int(threshold_votes),
        "threshold_pct": threshold_pct,
        "results": all_results
    }

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
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
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
                self.end_headers()
                self.wfile.write(content)
                return

        if path == "/api/ip":
            ip = self.get_client_ip()
            data = load_data()
            voted = ip in data.get("voted_ips", {})
            self.send_json({"ip": ip, "has_voted": voted})
            return

        if path == "/api/parties":
            self.send_json(PARTIES)
            return

        if path == "/api/results":
            stats = calculate_bader_ofer()
            self.send_json(stats)
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
            ip = self.get_client_ip()
            party_id = payload.get("party_id")

            if not party_id:
                self.send_json({"error": "נא לספק מזהה מפלגה"}, 400)
                return

            valid_party = next((p for p in PARTIES if p["id"] == party_id), None)
            if not valid_party:
                self.send_json({"error": "מפלגה לא חוקית"}, 400)
                return

            data = load_data()
            voted_ips = data.setdefault("voted_ips", {})

            if ip in voted_ips:
                self.send_json({
                    "error": f"כתובת ה-IP שלך ({ip}) כבר הצביעה במערכת. כל IP רשאי להצביע פעם אחת בלבד.",
                    "ip": ip,
                    "already_voted": True
                }, 403)
                return

            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            voted_ips[ip] = {
                "party_id": party_id,
                "party_letter": valid_party["letter"],
                "party_name": valid_party["name"],
                "timestamp": now_str
            }
            votes = data.setdefault("votes", {})
            votes[party_id] = votes.get(party_id, 0) + 1
            save_data(data)

            self.send_json({
                "success": True,
                "ip": ip,
                "party": valid_party["name"],
                "letter": valid_party["letter"],
                "timestamp": now_str
            })
            return

        if path == "/api/reset":
            initial = {
                "voted_ips": {},
                "votes": {p["id"]: 0 for p in PARTIES}
            }
            save_data(initial)
            self.send_json({"success": True, "message": "נתוני הקלפי אופסו בהצלחה"})
            return

        self.send_json({"error": "Endpoint not found"}, 404)

if __name__ == "__main__":
    load_data()
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    print(f"=====================================================")
    print(f"  🇮🇱 שרת בחירות 2026 לכנסת ה-26 פועל בכתובת:")
    print(f"  http://localhost:{port}")
    print(f"  הגבלת 1 הצבעה ל-IP & חלוקת 120 מנדטים בדר-עופר")
    print(f"=====================================================")
    with socketserver.TCPServer(("", port), ElectionHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nשרת הבחירות נעצר.")
