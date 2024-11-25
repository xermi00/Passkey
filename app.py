from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import logging

app = Flask(__name__)
CORS(app)
DB_PATH = "passkey.db"

logging.basicConfig(level=logging.INFO)

# Initialize the database
def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Create registrations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS registrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                status TEXT DEFAULT 'pending',
                elaboration TEXT
            )
        """)
        logging.info("Database initialized with registrations table.")
        conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Database initialization error: {e}")
    finally:
        if conn:
            conn.close()

@app.route('/register', methods=['POST'])
def register_username():
    username = request.form.get('username')

    if not username:
        return jsonify({"status": "failure", "message": "No username provided"}), 400

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Insert username as pending
        cursor.execute("INSERT INTO registrations (username) VALUES (?)", (username,))
        conn.commit()

        logging.info(f"Registration attempt by: {username}")
        return jsonify({"status": "success", "message": "Registration attempted"}), 200
    except sqlite3.IntegrityError:
        return jsonify({"status": "failure", "message": "Username already exists"}), 409
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return jsonify({"status": "failure", "message": "Database error occurred"}), 500
    finally:
        if conn:
            conn.close()

@app.route('/update_registration', methods=['POST'])
def update_registration():
    username = request.form.get('username')
    status = request.form.get('status')  # 'accepted' or 'declined'
    elaboration = request.form.get('elaboration', '')  # Optional

    if not username or not status:
        return jsonify({"status": "failure", "message": "Missing parameters"}), 400

    if status not in ["accepted", "declined"]:
        return jsonify({"status": "failure", "message": "Invalid status value"}), 400

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Update the username's status
        cursor.execute("""
            UPDATE registrations 
            SET status = ?, elaboration = ? 
            WHERE username = ?
        """, (status, elaboration, username))
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({"status": "failure", "message": "Username not found"}), 404

        logging.info(f"Updated registration for {username}: {status}")
        return jsonify({"status": "success", "message": "Registration updated successfully"}), 200
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return jsonify({"status": "failure", "message": "Database error occurred"}), 500
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
