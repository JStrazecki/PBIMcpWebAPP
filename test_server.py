"""
Minimal test server to verify deployment works
"""
import os
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"status": "test server working", "message": "deployment successful"})

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "test": "minimal server"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)