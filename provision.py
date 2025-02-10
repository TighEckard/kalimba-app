from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from twilio.rest import Client
import logging
from fastapi.middleware.cors import CORSMiddleware

# Create the FastAPI app instance.
app = FastAPI()

# Enable CORS for all origins (for testing purposes).
# Later you can change allow_origins to, for example, ["https://kalimba.world"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Twilio credentials – (for production, load these from environment variables)
TWILIO_ACCOUNT_SID = "AC2db3da2359ec7eea8ec8e63bdf06de42"  # Live Account SID
TWILIO_AUTH_TOKEN = "646b6f437a5879042d89fc05e1158f82"  # Live Auth Token


# Base domain used in your voice webhook URL (must be SSL-enabled)
BASE_DOMAIN = "kalimba.world"

# Initialize the Twilio client.
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

@app.post("/api/provision-number")
async def provision_number(desired_area_code: str = None, tenant_id: str = None):
    """
    Provisions a new phone number from Twilio.
    Optionally accepts a desired area code and tenant_id.
    The tenant_id is appended as a query parameter to the voice webhook URL.
    """
    try:
        # Set search parameters; limit results to 1.
        search_params = {"limit": 1}
        if desired_area_code:
            search_params["area_code"] = desired_area_code

        # Retrieve available US local phone numbers from Twilio.
        available_numbers = twilio_client.available_phone_numbers("US").local.list(**search_params)
        if not available_numbers:
            raise HTTPException(
                status_code=404,
                detail="No available phone numbers found for the specified area code."
            )

        # Select the first available phone number.
        selected_number = available_numbers[0].phone_number
        logging.info(f"Selected phone number: {selected_number}")

        # Construct the voice webhook URL.
        webhook_url = f"https://{BASE_DOMAIN}/incoming-call"
        if tenant_id:
            webhook_url += f"?tenant_id={tenant_id}"

        # Purchase the phone number and assign the webhook.
        purchased_number = twilio_client.incoming_phone_numbers.create(
            phone_number=selected_number,
            voice_url=webhook_url,
            voice_method="POST"
        )

        # Return the response as JSON.
        return JSONResponse({
            "phone_number": purchased_number.phone_number,
            "sid": purchased_number.sid,
            "voice_url": webhook_url,
            "message": "Phone number provisioned successfully."
        })
    except Exception as e:
        logging.error("Provisioning failed: " + str(e))
        raise HTTPException(status_code=500, detail=f"Provisioning failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
