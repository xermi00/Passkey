from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import logging

app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing
DB_PATH = "passkey.db"

logging.basicConfig(level=logging.INFO)

# Initialize the database
def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT UNIQUE,
                status TEXT,
                reason TEXT
            )
        """)
        conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Database initialization error: {e}")
    finally:
        if conn:
            conn.close()

@app.route('/')
def home():
    return jsonify({"message": "Registration service is running!"})

@app.route('/register', methods=['POST'])
def register_user():
    username = request.form.get('username')
    if not username:
        return jsonify({"status": "failure", "message": "No username provided"}), 400

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, status) VALUES (?, ?)", (username, "pending"))
        conn.commit()
        logging.info(f"{username} has tried to register.")
        return jsonify({"status": "success", "message": "Registration request sent."}), 200
    except sqlite3.IntegrityError:
        return jsonify({"status": "failure", "message": "Username already exists."}), 400
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return jsonify({"status": "failure", "message": "Database error occurred"}), 500
    finally:
        if conn:
            conn.close()

@app.route('/accept', methods=['POST'])
def accept_user():
    username = request.form.get('username')
    if not username:
        return jsonify({"status": "failure", "message": "No username provided"}), 400

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET status = 'accepted' WHERE username = ?", (username,))
        if cursor.rowcount == 0:
            return jsonify({"status": "failure", "message": "User not found."}), 404
        conn.commit()
        return jsonify({"status": "success", "message": "User accepted."}), 200
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return jsonify({"status": "failure", "message": "Database error occurred"}), 500
    finally:
        if conn:
            conn.close()

@app.route('/decline', methods=['POST'])
def decline_user():
    username = request.form.get('username')
    reason = request.form.get('reason')
    if not username or not reason:
        return jsonify({"status": "failure", "message": "Username and reason are required."}), 400

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET status = 'declined', reason = ? WHERE username = ?", (reason, username))
        if cursor.rowcount == 0:
            return jsonify({"status": "failure", "message": "User not found."}), 404
        conn.commit()
        return jsonify({"status": "success", "message": "User declined."}), 200
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return jsonify({"status": "failure", "message": "Database error occurred"}), 500
    finally:
        if conn:
            conn.close()

@app.route('/changeuser', methods=['POST'])
def change_username():
    current_username = request.form.get('current_username')
    new_username = request.form.get('new_username')

    if not current_username or not new_username:
        return jsonify({"status": "failure", "message": "Current and new username are required."}), 400

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET username = ? WHERE username = ?", (new_username, current_username))
        if cursor.rowcount == 0:
            return jsonify({"status": "failure", "message": "User not found."}), 404
        conn.commit()
        return jsonify({"status": "success", "message": "Username changed successfully."}), 200
    except sqlite3.IntegrityError:
        return jsonify({"status": "failure", "message": "New username already exists."}), 400
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return jsonify({"status": "failure", "message": "Database error occurred"}), 500
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
