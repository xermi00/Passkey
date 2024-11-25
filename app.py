from flask import Flask, request, jsonify
import sqlite3
import logging
import os

# Flask app setup
app = Flask(__name__)

# Database file path
DB_PATH = "passkey.db"

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def get_db_connection():
    """Connect to the database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Enable named column access
    return conn

@app.route('/register', methods=['POST'])
def register_user():
    """Register a new user."""
    try:
        data = request.get_json()
        username = data.get('username')

        if not username:
            return jsonify({"error": "Username is required."}), 400

        # Insert into registrations table
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO registrations (username, status)
            VALUES (?, 'pending')
        """, (username,))
        conn.commit()
        conn.close()

        logging.info(f"User '{username}' registered with 'pending' status.")
        return jsonify({"message": f"User '{username}' registered successfully with 'pending' status."}), 201

    except sqlite3.IntegrityError:
        return jsonify({"error": "Username already exists."}), 400
    except Exception as e:
        logging.error(f"Database error: {e}")
        return jsonify({"error": "Internal server error."}), 500

@app.route('/accept', methods=['POST'])
def accept_user():
    """Accept a user's registration."""
    try:
        data = request.get_json()
        username = data.get('username')

        if not username:
            return jsonify({"error": "Username is required."}), 400

        # Update status to 'accepted'
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE registrations
            SET status = 'accepted'
            WHERE username = ?
        """, (username,))
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({"error": f"User '{username}' not found."}), 404

        conn.commit()
        conn.close()

        logging.info(f"User '{username}' accepted.")
        return jsonify({"message": f"User '{username}' has been accepted."}), 200

    except Exception as e:
        logging.error(f"Database error: {e}")
        return jsonify({"error": "Internal server error."}), 500

@app.route('/decline', methods=['POST'])
def decline_user():
    """Decline a user's registration."""
    try:
        data = request.get_json()
        username = data.get('username')
        reason = data.get('reason', 'No reason provided.')

        if not username:
            return jsonify({"error": "Username is required."}), 400

        # Insert into decline_reasons table
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM registrations
            WHERE username = ?
        """, (username,))
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({"error": f"User '{username}' not found."}), 404

        cursor.execute("""
            INSERT INTO decline_reasons (username, reason)
            VALUES (?, ?)
        """, (username, reason))
        conn.commit()
        conn.close()

        logging.info(f"User '{username}' declined. Reason: {reason}")
        return jsonify({"message": f"User '{username}' has been declined.", "reason": reason}), 200

    except Exception as e:
        logging.error(f"Database error: {e}")
        return jsonify({"error": "Internal server error."}), 500

if __name__ == '__main__':
    if not os.path.exists(DB_PATH):
        logging.error("Database not found. Please initialize the database using 'init_db.py'.")
    else:
        app.run(debug=True)
