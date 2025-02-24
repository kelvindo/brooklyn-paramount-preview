from flask import Flask, request, jsonify, redirect
from flask_cors import CORS  # Import Flask-CORS
import requests
import os
from urllib.parse import quote

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes in your app

# --- Configuration ---
CLIENT_ID = os.environ.get('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = os.environ.get('SPOTIFY_CLIENT_SECRET')
REDIRECT_URI = 'http://localhost:8001'  # Match your http-server

if not CLIENT_ID or not CLIENT_SECRET:
    raise ValueError("Please set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET environment variables.")

# --- Authorization Endpoint ---
@app.route('/auth')
def auth():
    code = request.args.get('code')
    if not code:
        return jsonify({'error': 'Missing authorization code'}), 400

    token_url = 'https://accounts.spotify.com/api/token'
    payload = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    }
    try:
        response = requests.post(token_url, data=payload)
        response.raise_for_status()
        token_data = response.json()
        return jsonify(token_data)
    except requests.exceptions.RequestException as e:
        print(f"Error during token exchange: {e}")
        return jsonify({'error': 'Failed to exchange authorization code for token'}), 500

if __name__ == '__main__':
    app.run(port=8000)