                # Firebase may pass None when the election_data node does not exist yet.
                if not isinstance(current, dict):
                    current = _empty_data()

                # Normalize expected containers in case older/incomplete data exists.
                if not isinstance(current.get("voted_devices"), dict):
                    current["voted_devices"] = {}
                if not isinstance(current.get("voted_ips"), dict):
                    current["voted_ips"] = {}
                if not isinstance(current.get("votes"), dict):
                    current["votes"] = {}

                for party in PARTIES:
                    current["votes"].setdefault(party["id"], 0)

                # A device that has already voted must not increment the count again.
                if device_id in current["voted_devices"]:
                    return current

                current["voted_devices"][device_id] = {
                    "party_id": party_id,
                    "party_letter": valid["letter"],
                    "party_name": valid["name"],
                    "ip": client_ip,
                    "timestamp": now,
                    "_request_token": request_token,
                }
                current["voted_ips"][client_ip] = {
                    "party_id": party_id,
                    "timestamp": now,
                }
                current["votes"][party_id] = int(current["votes"].get(party_id, 0)) + 1
                current.setdefault("reset_id", 0)
                return current

            try:
                committed = FIREBASE_ROOT.transaction(apply_vote)
            except Exception as exc:
                print(
                    f"Firebase vote transaction failed: {type(exc).__name__}: {exc}",
                    flush=True
                )
                self.send_json(
                    {"error": "לא ניתן לשמור את ההצבעה כרגע. נסו שוב."},
                    503
                )
                return

            committed = committed if isinstance(committed, dict) else {}
            voted_devs = committed.get("voted_devices", {})
            saved_vote = voted_devs.get(device_id, {}) if isinstance(voted_devs, dict) else {}
            votes = committed.get("votes", {})


            if saved_vote.get("_request_token") != request_token:
                self.send_json({
                    "error": "מכשיר זה כבר ביצע הצבעה במערכת זו.",
                    "already_voted": True,
                    "votes": votes,
                    "total_votes": sum(votes.values()) if isinstance(votes, dict) else 0,
                    "voted_count": len(voted_devs) if isinstance(voted_devs, dict) else 0
                }, 403)
                return

            self.send_json({
                "success": True,
                "votes": votes,
                "total_votes": sum(votes.values()) if isinstance(votes, dict) else 0,
                "voted_count": len(voted_devs) if isinstance(voted_devs, dict) else 0,
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
            def reset_data(_current):
                return {
                    "voted_devices": {},
                    "voted_ips": {},
                    "votes": {p["id"]: 0 for p in PARTIES},
                    "reset_id": int(datetime.now().timestamp())
                }
            try:
                data = FIREBASE_ROOT.transaction(reset_data)
            except Exception as exc:
                print(f"Firebase reset transaction failed: {exc}")
                self.send_json({"error": "איפוס נכשל. נסו שוב."}, 503)
                return
            res_votes = dict(data.get("votes", {}))
            self.send_json({
                "success": True,
                "votes": res_votes,
                "total_votes": 0,
                "voted_count": 0,
                "reset_id": data.get("reset_id", 0)
            })
            return

        if path == "/api/admin/inject":
            self.send_json({"error": "הנתיב אינו זמין בגרסת הפרסום"}, 404)
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
