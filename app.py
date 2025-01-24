from flask_cors import CORS
CORS(app)
from flask import Flask, request, jsonify

app = Flask(__name__)

# Store the password in memory
current_password = "default_password"

@app.route('/validate', methods=['POST'])
def validate_password():
    global current_password
    submitted_password = request.form.get('password')
    if submitted_password == current_password:
        return jsonify(True)
    else:
        return jsonify(False)

@app.route('/update_password', methods=['POST'])
def update_password():
    global current_password
    new_password = request.form.get('new_password')
    if new_password:
        current_password = new_password
        return "Password updated successfully.", 200
    else:
        return "Failed to update password. Provide a valid password.", 400

if __name__ == '__main__':
    app.run(debug=True)
