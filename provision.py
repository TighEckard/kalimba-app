from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from twilio.rest import Client
import logging

app = FastAPI()

# Twilio credentials – ideally, load these from environment variables
TWILIO_ACCOUNT_SID = "AC2db3da2359ec7eea8ec8e63bdf06de42"
TWILIO_AUTH_TOKEN = "646b6f437a5879042d89fc05e1158f82"

# Your domain (must be SSL-enabled)
BASE_DOMAIN = "kalimba.world"  # Replace with your website domain

# Initialize Twilio client
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

@app.post("/api/provision-number")
async def provision_number(desired_area_code: str = None, tenant_id: str = None):
    """
    Provisions a new phone number from Twilio.
    Optionally accepts a desired area code and tenant_id.
    The tenant_id will be appended as a query parameter to the voice webhook.
    """
    try:
        # Search for an available local phone number (US numbers)
        search_params = {"limit": 1}
        if desired_area_code:
            search_params["area_code"] = desired_area_code

        available_numbers = twilio_client.available_phone_numbers("US").local.list(**search_params)
        if not available_numbers:
            raise HTTPException(status_code=404, detail="No available phone numbers found for the specified area code.")
        
        selected_number = available_numbers[0].phone_number
        logging.info(f"Selected phone number: {selected_number}")
        
        # Build the webhook URL that points to your call-handling endpoint.
        # The tenant_id is included (if provided) for tenant-specific configuration.
        webhook_url = f"https://{BASE_DOMAIN}/incoming-call"
        if tenant_id:
            webhook_url += f"?tenant_id={tenant_id}"
        
        # Purchase the phone number and configure its voice URL.
        purchased_number = twilio_client.incoming_phone_numbers.create(
            phone_number=selected_number,
            voice_url=webhook_url,
            voice_method="POST"
        )
        
        # (Optional) Store purchased_number.phone_number and tenant_id in your database.
        
        return JSONResponse({
            "phone_number": purchased_number.phone_number,
            "sid": purchased_number.sid,
            "voice_url": webhook_url,
            "message": "Phone number provisioned successfully."
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Provisioning failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
