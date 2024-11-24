from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)
DB_PATH = "passkey.db"

# Verify the passkey
@app.route('/verify', methods=['POST'])
def verify_passkey():
    user_passkey = request.form.get('passkey')

    if not user_passkey:
        return jsonify({"status": "failure", "message": "No passkey provided"}), 400

    try:
        # Open a connection to the database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Query for the stored passkey
        cursor.execute("SELECT key FROM passkey")
        stored_passkey = cursor.fetchone()

        # If no passkey is found, return an error
        if stored_passkey is None:
            return jsonify({"status": "failure", "message": "No passkey stored"}), 404

        # Check if the provided passkey matches the stored one
        if user_passkey == stored_passkey[0]:
            return jsonify({"status": "success"}), 200
        else:
            return jsonify({"status": "failure", "message": "Incorrect passkey"}), 401
    except sqlite3.Error as e:
        return jsonify({"status": "failure", "message": str(e)}), 500
    finally:
        if conn:
            conn.close()  # Ensure the database connection is always closed

# Update the passkey
@app.route('/update', methods=['POST'])
def update_passkey():
    new_passkey = request.form.get('passkey')

    if not new_passkey:
        return jsonify({"status": "failure", "message": "No passkey provided"}), 400

    try:
        # Open a connection to the database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Update the passkey in the database
        cursor.execute("UPDATE passkey SET key = ?", (new_passkey,))
        conn.commit()
    except sqlite3.Error as e:
        return jsonify({"status": "failure", "message": str(e)}), 500
    finally:
        if conn:
            conn.close()  # Ensure the database connection is always closed

    return jsonify({"status": "passkey updated"}), 200

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
