import os
from flask import Flask, request, Response  # type: ignore
import stripe # type: ignore
from twilio.rest import Client as TwilioClient # type: ignore
from twilio.twiml.voice_response import VoiceResponse # type: ignore
from dotenv import load_dotenv # type: ignore

load_dotenv()

app = Flask(__name__)

# Configure Stripe
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
stripe_webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET")

# Configure Twilio
twilio_account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
twilio_auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
twilio_client = TwilioClient(twilio_account_sid, twilio_auth_token)

@app.route('/stripe-webhook', methods=['POST'])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, stripe_webhook_secret
        )
    except Exception as e:
        print("Webhook signature verification failed:", e)
        return Response(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        user_id = session.get('metadata', {}).get('userId')
        if user_id:
            try:
                purchased_number = provision_user_phone_number(user_id)
                print(f"Provisioned phone number {purchased_number.phone_number} for user {user_id}")
            except Exception as e:
                print("Error provisioning phone number:", e)
    return Response(status=200)

@app.route('/ai-receptionist', methods=['POST'])
def ai_receptionist():
    response = VoiceResponse()
    response.say("Welcome to your AI receptionist. Please wait while we connect you.")
    return Response(str(response), mimetype='text/xml')

def provision_user_phone_number(user_id):
    available_numbers = twilio_client.available_phone_numbers('US').local.list(limit=1)
    if not available_numbers:
        raise Exception("No available phone numbers found")
    selected_number = available_numbers[0].phone_number
    purchased_number = twilio_client.incoming_phone_numbers.create(
        phone_number=selected_number,
        voice_url='https://yourdomain.com/ai-receptionist',  # Replace with your actual endpoint URL
        voice_method='POST'
    )
    save_user_phone_number_config(user_id, {
        'phone_number': purchased_number.phone_number,
        'prompt': '',
        'redirection': ''
    })
    return purchased_number

def save_user_phone_number_config(user_id, config):
    print(f"Saving config for user {user_id}: {config}")
    # Replace with actual database code if needed

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 3000))
    app.run(host='0.0.0.0', port=port)
