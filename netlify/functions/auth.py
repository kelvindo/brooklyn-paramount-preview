import requests
import os
from urllib.parse import quote
import json

# --- Configuration (Environment Variables) ---
CLIENT_ID = os.environ.get('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = os.environ.get('SPOTIFY_CLIENT_SECRET')
# No REDIRECT_URI here - it's handled client-side

def lambda_handler(event, context):  # Standard Lambda handler signature
    code = event['queryStringParameters'].get('code')
    # Use Netlify's redirect URI - this will point to your deployed site
    redirect_uri = os.environ.get('URL') + '/'  # Get base URL from Netlify environment

    if not code or not CLIENT_ID or not CLIENT_SECRET:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Missing parameters'})
        }

    token_url = 'https://accounts.spotify.com/api/token'
    payload = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri,  # Use the dynamically generated URI
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    }

    try:
        response = requests.post(token_url, data=payload)
        response.raise_for_status()
        token_data = response.json()
        # Return the token data as a JSON response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',  # Important for CORS with Netlify
                'Access-Control-Allow-Headers': 'Content-Type',
            },
            'body': json.dumps(token_data)
        }

    except requests.exceptions.RequestException as e:
        print(f"Error during token exchange: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Failed to exchange authorization code for token'})
        }