from flask import Flask, request, jsonify
from flask_cors import CORS

# Create the Flask application instance
app = Flask(__name__)

# Apply CORS to the app
CORS(app, resources={r"/*": {"origins": "*"}})

# Store the password and server status in memory
current_password = "default_password"
server_status = "Server is live!"

@app.route('/validate', methods=['POST'])
def validate_password():
    global current_password
    submitted_password = request.form.get('password')
    if submitted_password == current_password:
        return jsonify(True)
    else:
        return jsonify(False)

@app.route('/current_password', methods=['GET'])
def get_current_password():
    global current_password
    return jsonify({
        "status": "success",
        "password": current_password
    }), 200

@app.route('/update_password', methods=['POST'])
def update_password():
    global current_password
    new_password = request.form.get('new_password')
    if new_password:
        current_password = new_password
        return "Password updated successfully.", 200
    else:
        return "Failed to update password. Provide a valid password.", 400

@app.route('/health', methods=['GET'])
def health_check():
    global server_status
    return jsonify({
        "status": "success",
        "message": server_status
    }), 200

if __name__ == '__main__':
    app.run(debug=True)
