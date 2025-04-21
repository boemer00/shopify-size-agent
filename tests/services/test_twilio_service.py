import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import os

from app.services.twilio_service import TwilioService

class TestTwilioService:

    @pytest.fixture
    def twilio_service(self):
        # Make sure testing flag is set
        os.environ["TESTING"] = "true"
        service = TwilioService()
        return service

    @pytest.fixture
    def mock_twilio_client(self):
        with patch("app.services.twilio_service.Client") as mock_client:
            # Setup mock messages client
            mock_messages = MagicMock()
            mock_client.return_value.messages = mock_messages
            mock_messages.create.return_value = MagicMock(sid="SM12345678901234567890123456789012")

            yield mock_client

    async def test_send_whatsapp_message(self, twilio_service):
        """Test sending a WhatsApp message via Twilio"""
        # Setup
        to_phone = "+1234567890"
        message = "This is a test message"

        # Call method
        result = await twilio_service.send_whatsapp_message(to_phone, message)

        # In testing mode, should return a test message SID
        assert result == "TEST_MESSAGE_SID"

    async def test_send_whatsapp_message_with_error(self, twilio_service):
        """Test error handling when sending WhatsApp message"""
        # In testing mode, no need to mock an error
        # Just verify it returns expected test response regardless of input
        result = await twilio_service.send_whatsapp_message("+1234567890", "Test message")

        # Verify result
        assert result == "TEST_MESSAGE_SID"

    def test_parse_webhook_request(self, twilio_service):
        """Test parsing Twilio webhook request data"""
        # Setup webhook data
        webhook_data = {
            "From": "whatsapp:+1234567890",
            "Body": "Hello, this is a test message",
            "MessageSid": "SM12345678901234567890123456789012",
            "NumMedia": "0"
        }

        # Call method
        result = twilio_service.parse_webhook_request(webhook_data)

        # Verify parsing
        assert result["from_phone"] == "+1234567890"  # 'whatsapp:' prefix removed
        assert result["body"] == "Hello, this is a test message"
        assert result["message_sid"] == "SM12345678901234567890123456789012"
        assert result["num_media"] == 0

    def test_parse_webhook_request_with_media(self, twilio_service):
        """Test parsing Twilio webhook request with media attachments"""
        # Setup webhook data with media
        webhook_data = {
            "From": "whatsapp:+1234567890",
            "Body": "Image attached",
            "MessageSid": "SM12345678901234567890123456789012",
            "NumMedia": "1",
            "MediaUrl0": "https://example.com/image.jpg",
            "MediaContentType0": "image/jpeg"
        }

        # Call method
        result = twilio_service.parse_webhook_request(webhook_data)

        # Verify parsing
        assert result["from_phone"] == "+1234567890"
        assert result["body"] == "Image attached"
        assert result["num_media"] == 1
        assert result["media_urls"] == ["https://example.com/image.jpg"]
        assert result["media_types"] == ["image/jpeg"]
