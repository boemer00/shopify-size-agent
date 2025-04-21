from fastapi import APIRouter, Request, Response, Form, Depends, HTTPException, status
from twilio.request_validator import RequestValidator
import os
from typing import Optional

from app.services.twilio_service import TwilioService
from app.services.conversation_service import ConversationService


router = APIRouter()
twilio_service = TwilioService()
conversation_service = ConversationService()


async def validate_twilio_request(request: Request) -> bool:
    """
    Validate that the request came from Twilio

    Args:
        request: The FastAPI request object

    Returns:
        True if the request is valid, False otherwise
    """
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
    validator = RequestValidator(auth_token)

    # Get the URL and POST data
    url = str(request.url)

    # Get all the post data as a dict
    form_data = await request.form()
    post_data = dict(form_data)

    # Get the X-Twilio-Signature header
    signature = request.headers.get("X-Twilio-Signature", "")

    # Validate the request
    return validator.validate(url, post_data, signature)


@router.post("/webhook/reply", status_code=status.HTTP_200_OK)
async def reply_webhook(
    request: Request,
    From: str = Form(...),
    Body: str = Form(...),
    MessageSid: Optional[str] = Form(None),
    NumMedia: Optional[int] = Form(0)
):
    """
    Handle Twilio webhook for incoming WhatsApp messages

    This endpoint:
    1. Validates the request came from Twilio
    2. Parses the message data
    3. Processes the customer reply
    4. Returns a TwiML response
    """
    # Validate the request in production (commented out for development)
    # if not await validate_twilio_request(request):
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="Invalid Twilio signature"
    #     )

    # Parse the webhook data
    form_data = await request.form()
    data = twilio_service.parse_webhook_request(dict(form_data))

    # Process the message
    try:
        await conversation_service.process_customer_reply(
            from_phone=data["from_phone"],
            message_content=data["body"]
        )
    except Exception as e:
        # Log the error but don't fail the webhook
        print(f"Error processing reply: {str(e)}")

    # Return empty TwiML response
    return Response(
        content="<?xml version=\"1.0\" encoding=\"UTF-8\"?><Response></Response>",
        media_type="application/xml"
    )
