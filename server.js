// Load environment variables from .env file
require('dotenv').config();

const express = require('express');
const bodyParser = require('body-parser');
const twilio = require('twilio');

const app = express();
const PORT = process.env.PORT || 3000;

// Create Twilio client using your credentials
const twilioClient = twilio(process.env.TWILIO_ACCOUNT_SID, process.env.TWILIO_AUTH_TOKEN);

// Parse JSON bodies (incoming data)
app.use(express.json());

// Allow serving static files (for our HTML page later)
app.use(express.static('public'));

/**
 * Endpoint to search for available phone numbers.
 * It expects a JSON payload with "query" (e.g., an area code or digits).
 * It returns up to 3 available phone numbers.
 */
app.post('/api/search-numbers', async (req, res) => {
  const { query } = req.body;
  try {
    // If query is all digits, assume it's an area code
    const searchOptions = {};
    if (/^\d+$/.test(query)) {
      searchOptions.areaCode = query;
    } else {
      searchOptions.contains = query;
    }
    const availableNumbers = await twilioClient.availablePhoneNumbers('US').local.list({
      ...searchOptions,
      limit: 3
    });
    const numbers = availableNumbers.map(num => num.phoneNumber);
    res.json({ numbers });
  } catch (error) {
    console.error("Error fetching numbers:", error);
    res.status(500).json({ error: "Unable to fetch numbers." });
  }
});

/**
 * Endpoint to provision (purchase) a phone number.
 * It expects a JSON payload with "selected_number".
 * It returns the purchased number.
 */
app.post('/api/provision-number', async (req, res) => {
  const { selected_number } = req.body;
  try {
    const purchasedNumber = await twilioClient.incomingPhoneNumbers.create({
      phoneNumber: selected_number,
      // Set the voice URL to your AI endpoint (update this URL when you have a domain)
      voiceUrl: 'https://yourdomain.com/ai-receptionist',
      voiceMethod: 'POST'
    });
    // Here you would save the number and its (initially empty) configuration
    // (For now, we simply return the purchased number.)
    res.json({ phone_number: purchasedNumber.phoneNumber });
  } catch (error) {
    console.error("Error provisioning number:", error);
    res.status(500).json({ error: "Unable to provision number." });
  }
});

// (Later you will add an endpoint here to update a phone number's configuration.)

// Start the server
app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});
