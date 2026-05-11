export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  const { name, email, company, usecase } = req.body;
  if (!name || !email) return res.status(400).json({ error: 'Name and email required' });

  try {
    // Get fresh access token
    const tokenRes = await fetch('https://oauth2.googleapis.com/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        client_id:     process.env.GOOGLE_CLIENT_ID,
        client_secret: process.env.GOOGLE_CLIENT_SECRET,
        refresh_token: process.env.GOOGLE_REFRESH_TOKEN,
        grant_type:    'refresh_token',
      }),
    });
    const { access_token } = await tokenRes.json();

    // Append row to Google Sheet
    const sheetRes = await fetch(
      `https://sheets.googleapis.com/v4/spreadsheets/${process.env.SHEET_ID}/values/Sheet1!A1:append?valueInputOption=USER_ENTERED&insertDataOption=INSERT_ROWS`,
      {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          values: [[new Date().toLocaleString('en-US', { timeZone: 'America/New_York' }), name, email, company || '', usecase || '']],
        }),
      }
    );

    if (!sheetRes.ok) {
      const err = await sheetRes.text();
      throw new Error(err);
    }

    return res.status(200).json({ status: 'ok' });
  } catch (err) {
    console.error(err);
    return res.status(500).json({ error: 'Failed to save' });
  }
}
