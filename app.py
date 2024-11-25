from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import logging

app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing
DB_PATH = "passkey.db"

# Set up logging
logging.basicConfig(level=logging.INFO)

# Initialize the database
def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                status TEXT,   -- "pending", "accepted", "declined"
                elaboration TEXT
            )
        """)
        conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Database initialization error: {e}")
    finally:
        if conn:
            conn.close()

# Root route
@app.route('/')
def home():
    return jsonify({"message": "Registration verification service is running!"})

# Handle registration attempts
@app.route('/register', methods=['POST'])
def register_user():
    username = request.form.get('username')

    if not username:
        return jsonify({"status": "failure", "message": "No username provided"}), 400

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check if the user is already registered
        cursor.execute("SELECT status FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()

        if user:
            return jsonify({"status": "failure", "message": f"Username already {user[0]}"}), 400

        # Insert new user with pending status
        cursor.execute("INSERT INTO users (username, status) VALUES (?, 'pending')", (username,))
        conn.commit()
        logging.info(f"User '{username}' attempted registration.")
        return jsonify({"status": "pending", "message": "Registration pending approval"}), 200
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return jsonify({"status": "failure", "message": "Database error occurred"}), 500
    finally:
        if conn:
            conn.close()

# Approve or decline registration
@app.route('/review', methods=['POST'])
def review_registration():
    username = request.form.get('username')
    action = request.form.get('action')  # "accept" or "decline"
    elaboration = request.form.get('elaboration', '')

    if not username or action not in ("accept", "decline"):
        return jsonify({"status": "failure", "message": "Invalid input"}), 400

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Update the user's status
        if action == "accept":
            cursor.execute("UPDATE users SET status = 'accepted', elaboration = NULL WHERE username = ?", (username,))
            conn.commit()
            return jsonify({"status": "success", "message": "User accepted"}), 200
        elif action == "decline":
            cursor.execute("UPDATE users SET status = 'declined', elaboration = ? WHERE username = ?", (elaboration, username))
            conn.commit()
            return jsonify({"status": "success", "message": "User declined"}), 200
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return jsonify({"status": "failure", "message": "Database error occurred"}), 500
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
