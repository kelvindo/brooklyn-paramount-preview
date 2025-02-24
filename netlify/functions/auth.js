const fetch = require('node-fetch'); // Use node-fetch for server-side requests
const querystring = require('querystring');

exports.handler = async (event, context) => {
  const code = event.queryStringParameters.code;
  const redirect_uri = process.env.URL + '/'; // Get base URL from Netlify environment

  const CLIENT_ID = process.env.SPOTIFY_CLIENT_ID;
  const CLIENT_SECRET = process.env.SPOTIFY_CLIENT_SECRET;


  if (!code || !CLIENT_ID || !CLIENT_SECRET) {
    return {
      statusCode: 400,
      body: JSON.stringify({ error: 'Missing parameters' }),
    };
  }

  const tokenUrl = 'https://accounts.spotify.com/api/token';
  const payload = {
    grant_type: 'authorization_code',
    code: code,
    redirect_uri: redirect_uri,
    client_id: CLIENT_ID,
    client_secret: CLIENT_SECRET,
  };

  try {
    const response = await fetch(tokenUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded', // Important for Spotify
      },
      body: querystring.stringify(payload), // Use querystring.stringify
    });

    const tokenData = await response.json();

    if (!response.ok) {
      throw new Error(`Token exchange failed: ${response.status} ${JSON.stringify(tokenData)}`);
    }

    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*', // Important for CORS
        'Access-Control-Allow-Headers': 'Content-Type',
      },
      body: JSON.stringify(tokenData),
    };

  } catch (error) {
    console.error("Error during token exchange:", error);
    return {
      statusCode: 500,
      body: JSON.stringify({ error: 'Failed to exchange authorization code for token' }),
    };
  }
};