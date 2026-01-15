from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# 🔑 KEYS
MASTER_KEY = "AyushloveAyushi"
VALID_KEYS = {"USER_1", "USER_2"}

TC_URL = "https://search5-noneu.truecaller.com/v2/search"
TC_HEADERS = {
    "User-Agent": "Truecaller/16.7.8 (Android;15)",
    "Accept": "application/json",
    "Accept-Encoding": "identity",   # 🔥 important for vercel/render
    "authorization": "Bearer a2i0s--yWJylvVeF5FNGuh_MJUR2txVpAypP6YUD8otXzdsGeFywFDMok8-DqMou"
}

@app.route("/lookup")
def lookup():
    key = request.args.get("key")
    number = request.args.get("number")

    if not key or not number:
        return jsonify({"status": False, "error": "missing params"}), 400

    if key != MASTER_KEY and key not in VALID_KEYS:
        return jsonify({"status": False, "error": "invalid key"}), 403

    r = requests.get(
        TC_URL,
        params={
            "q": number,
            "countryCode": "IN",
            "type": 4,
            "encoding": "json"
        },
        headers=TC_HEADERS,
        timeout=10
    )

    # ❌ blocked / empty / non-200
    if r.status_code != 200 or not r.text.strip():
        return jsonify({
            "status": False,
            "error": "upstream blocked or empty",
            "http_status": r.status_code
        }), 502

    # ❌ not json
    if "application/json" not in r.headers.get("content-type", ""):
        return jsonify({
            "status": False,
            "error": "non-json response from provider",
            "http_status": r.status_code
        }), 502

    try:
        raw = r.json()
    except Exception:
        return jsonify({
            "status": False,
            "error": "json decode failed"
        }), 502

    out = []

    for d in raw.get("data", []):
        phone = (d.get("phones") or [{}])[0]
        addr = (d.get("addresses") or [{}])[0]
        mail = (d.get("internetAddresses") or [{}])[0]

        out.append({
            "name": d.get("name"),
            "gender": d.get("gender"),
            "isFraud": d.get("isFraud"),
            "manualCallerIdPrompt": d.get("manualCallerIdPrompt"),

            "address": {
                "city": addr.get("city"),
                "countryCode": addr.get("countryCode"),
                "timeZone": addr.get("timeZone"),
                "type": addr.get("type"),
                "value": addr.get("address")
            },

            "internet": {
                "id": mail.get("id"),
                "caption": mail.get("caption"),
                "service": mail.get("service")
            },

            "phone": {
                "carrier": phone.get("carrier"),
                "dialingCode": phone.get("dialingCode"),
                "e164Format": phone.get("e164Format"),
                "nationalFormat": phone.get("nationalFormat"),
                "numberType": phone.get("numberType")
            }
        })

    return jsonify({
        "status": True,
        "master": key == MASTER_KEY,
        "result": out
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
