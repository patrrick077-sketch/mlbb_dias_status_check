from flask import Flask, request, jsonify
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

# Headers
headers_meyan = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36",
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": "https://meyangameshop.com",
    "Referer": "https://meyangameshop.com/",
}

headers_smile = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36",
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": "https://www.smile.one",
    "Referer": "https://www.smile.one/",
}

def check_meyan(user_id, zone_id):
    url = "https://meyangameshop.com/checkml"
    payload = {"id": user_id, "zone": zone_id}
    try:
        r = requests.post(url, data=payload, headers=headers_meyan, timeout=12)
        if r.status_code == 200:
            data = r.json()
            available = [k for k, v in data.get("dd", {}).items() if v is True]
            return available
    except:
        pass
    return []

def check_smile(user_id, zone_id):
    url = "https://www.smile.one/merchant/mobilelegends/checkrole"
    payload = {
        "user_id": user_id,
        "zone_id": zone_id,
        "pid": "25",
        "checkrole": "1",
        "pay_method": "",
        "channel_method": ""
    }
    try:
        r = requests.post(url, data=payload, headers=headers_smile, timeout=12)
        if r.status_code == 200:
            data = r.json()
            return {
                "username": data.get("username", "Not found"),
                "zone": data.get("zone")          # ← Real zone from Smile (e.g. 1)
            }
    except:
        pass
    return {"username": "Not found", "zone": None}

@app.route('/check', methods=['GET'])
def check_ml():
    user_id = request.args.get('uid')
    zone_id = request.args.get('sid')

    if not user_id or not zone_id:
        return jsonify({"error": "Missing uid or sid parameter"}), 400

    # Concurrent execution for speed
    with ThreadPoolExecutor(max_workers=2) as executor:
        future_meyan = executor.submit(check_meyan, user_id, zone_id)
        future_smile = executor.submit(check_smile, user_id, zone_id)

        available_packages = future_meyan.result()
        player_info = future_smile.result()

    # Final response with BOTH zone_id (input) and real zone (from API)
    response = {
        "status": "success",
        "username": player_info.get("username"),
        "zone_id": zone_id,                    # your sid
        "zone": player_info.get("zone"),       # ← real zone from Smile (e.g. 1)
        "available_topup": available_packages,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    return jsonify(response), 200

# Test page
@app.route('/')
def home():
    return """
    <h1>MHM MLBB Checker API</h1>
    <p>Use: <code>/check?uid=896334313&sid=12559</code></p>
    <p>Example: http://10.10.10.20:5000/check?uid=896334313&sid=12559</p>
    """

if __name__ == '__main__':
    print("MHM MLBB Checker API running on http://0.0.0.0:5000")
    print("Endpoint: /check?uid=XXX&sid=XXX")
    print("Concurrent ThreadPool activated")
    app.run(host='0.0.0.0', port=5000, debug=True)
