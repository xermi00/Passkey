from flask import Flask, request, jsonify
import sqlite3
import logging

# Flask app setup
app = Flask(__name__)
DB_PATH = "passkey.db"
logging.basicConfig(level=logging.INFO)

# Database initialization
def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Create the registrations table if it doesn't exist
        cursor.execute('''CREATE TABLE IF NOT EXISTS registrations (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT UNIQUE NOT NULL,
                            status TEXT DEFAULT 'pending'
                          )''')
        conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Database initialization error: {e}")
    finally:
        if conn:
            conn.close()

# Register a username
@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')

    # Validate the username
    if not username or len(username) > 15 or ' ' in username:
        return jsonify({"status": "failure", "message": "Invalid username"}), 400

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check if the username already exists
        cursor.execute("SELECT COUNT(*) FROM registrations WHERE username = ?", (username,))
        if cursor.fetchone()[0] > 0:
            return jsonify({"status": "failure", "message": "Username already registered"}), 409

        # Insert the new username
        cursor.execute("INSERT INTO registrations (username) VALUES (?)", (username,))
        conn.commit()

        # Log the registration for moderation
        logging.info(f"{username} has tried to register.")
        return jsonify({"status": "pending", "message": f"{username} has been added for review"}), 200
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return jsonify({"status": "failure", "message": "Database error"}), 500
    finally:
        if conn:
            conn.close()

# Moderate a registration (accept or decline)
@app.route('/moderate', methods=['POST'])
def moderate():
    action = request.form.get('action')
    username = request.form.get('username')

    # Validate the action
    if action not in ['accept', 'decline']:
        return jsonify({"status": "failure", "message": "Invalid action"}), 400

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check if the username exists
        cursor.execute("SELECT COUNT(*) FROM registrations WHERE username = ?", (username,))
        if cursor.fetchone()[0] == 0:
            return jsonify({"status": "failure", "message": "Username not found"}), 404

        if action == "accept":
            cursor.execute("UPDATE registrations SET status = 'accepted' WHERE username = ?", (username,))
            logging.info(f"{username} has been accepted.")
        elif action == "decline":
            cursor.execute("DELETE FROM registrations WHERE username = ?", (username,))
            logging.info(f"{username} has been declined.")

        conn.commit()
        return jsonify({"status": "success", "message": f"{username} has been {action}ed."}), 200
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return jsonify({"status": "failure", "message": "Database error"}), 500
    finally:
        if conn:
            conn.close()

# List all pending registrations
@app.route('/pending', methods=['GET'])
def get_pending():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Fetch all pending registrations
        cursor.execute("SELECT username FROM registrations WHERE status = 'pending'")
        pending = [row[0] for row in cursor.fetchall()]

        return jsonify({"status": "success", "pending": pending}), 200
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return jsonify({"status": "failure", "message": "Database error"}), 500
    finally:
        if conn:
            conn.close()

# Initialize the database on startup
if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
