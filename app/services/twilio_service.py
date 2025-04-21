import os
from twilio.rest import Client
from typing import Optional, Dict, List, Any


class TwilioService:
    def __init__(self):
        # Check if we're in testing mode
        self.testing = os.environ.get("TESTING", "").lower() == "true"

        self.account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        self.auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
        self.from_phone = os.environ.get("TWILIO_PHONE_NUMBER")

        # Initialize Twilio client only if not in testing mode
        if not self.testing:
            try:
                self.client = Client(self.account_sid, self.auth_token)
            except Exception as e:
                print(f"Warning: Could not initialize Twilio client: {e}")
                self.client = None
        else:
            self.client = None

    async def send_whatsapp_message(self, to_phone: str, message: str) -> Optional[str]:
        """
        Send a WhatsApp message through Twilio

        Args:
            to_phone: The recipient's phone number in E.164 format (e.g., +1234567890)
            message: The message content to send

        Returns:
            The Twilio message SID or None if in testing mode or on error
        """
        if self.testing:
            print(f"[TEST] Would send WhatsApp message to {to_phone}: {message}")
            return "TEST_MESSAGE_SID"

        if not self.client or not self.from_phone:
            print("Cannot send message: Twilio client not initialized or from_phone not set")
            return None

        try:
            # Format numbers for WhatsApp
            from_whatsapp = f"whatsapp:{self.from_phone}"
            to_whatsapp = f"whatsapp:{to_phone}"

            # Send the message
            message = self.client.messages.create(
                body=message,
                from_=from_whatsapp,
                to=to_whatsapp
            )

            return message.sid
        except Exception as e:
            print(f"Error sending WhatsApp message: {e}")
            return None

    # Alias for backward compatibility
    async def send_message(self, to_phone: str, message: str) -> Optional[str]:
        """
        Alias for send_whatsapp_message for backward compatibility

        Args:
            to_phone: The recipient's phone number
            message: The message content

        Returns:
            The Twilio message SID or None
        """
        return await self.send_whatsapp_message(to_phone=to_phone, message=message)

    def parse_webhook_request(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse the incoming webhook request from Twilio

        Args:
            form_data: The form data from the Twilio webhook

        Returns:
            A dictionary with parsed data
        """
        parsed_data = {
            "message_sid": form_data.get("MessageSid", ""),
            "from_phone": form_data.get("From", "").replace("whatsapp:", ""),
            "to_phone": form_data.get("To", "").replace("whatsapp:", ""),
            "body": form_data.get("Body", ""),
            "num_media": int(form_data.get("NumMedia", "0")),
            "media_urls": [],
            "media_types": []
        }

        # Extract media if present
        for i in range(parsed_data["num_media"]):
            media_url = form_data.get(f"MediaUrl{i}")
            media_type = form_data.get(f"MediaContentType{i}")

            if media_url:
                parsed_data["media_urls"].append(media_url)

            if media_type:
                parsed_data["media_types"].append(media_type)

        return parsed_data
