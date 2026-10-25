                if device_id in voted_devs:
                    self.send_json({
                        "error": "מכשיר זה כבר ביצע הצבעה במערכת זו.",
                        "already_voted": True,
                        "votes": data["votes"],
                        "total_votes": sum(data["votes"].values()),
                        "voted_count": len(voted_devs)
                    }, 403)
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
