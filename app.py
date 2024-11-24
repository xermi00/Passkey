from flask import Flask, request, jsonify
import sqlite3
from waitress import serve

app = Flask(__name__)
DB_PATH = "passkey.db"

# Verify the passkey
@app.route('/verify', methods=['POST'])
def verify_passkey():
    user_passkey = request.form.get('passkey')
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT key FROM passkey")
    stored_passkey = cursor.fetchone()[0]
    conn.close()

    if user_passkey == stored_passkey:
        return jsonify({"status": "success"}), 200
    else:
        return jsonify({"status": "failure"}), 401

# Update the passkey
@app.route('/update', methods=['POST'])
def update_passkey():
    new_passkey = request.form.get('passkey')
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE passkey SET key = ?", (new_passkey,))
    conn.commit()
    conn.close()
    return jsonify({"status": "passkey updated"}), 200

# Run the app with Waitress
if __name__ == "__main__":
    print("Starting Flask app with Waitress...")
    serve(app, host="0.0.0.0", port=5000)
