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
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/register', methods=['POST'])
def register_user():
    """Register a new user."""
    try:
        data = request.get_json()
        if not data or 'username' not in data:
            return jsonify({"error": "Username is required."}), 400

        username = data['username'].strip()

        if not username or len(username) > 15 or " " in username:
            return jsonify({"error": "Invalid username. Ensure it is non-empty, no spaces, and <= 15 characters."}), 400

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
        if not data or 'username' not in data:
            return jsonify({"error": "Username is required."}), 400

        username = data['username'].strip()
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
        if not data or 'username' not in data or 'reason' not in data:
            return jsonify({"error": "Username and reason are required."}), 400

        username = data['username'].strip()
        reason = data['reason'].strip()

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
