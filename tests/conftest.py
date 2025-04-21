import pytest
from unittest.mock import MagicMock, AsyncMock
from uuid import UUID

@pytest.fixture
def mock_supabase_service():
    service = AsyncMock()

    # Mock customer data
    service.get_customer_by_shopify_id.return_value = None
    service.get_customer_by_phone.return_value = MagicMock(
        id=UUID("12345678-1234-5678-1234-567812345678"),
        shopify_customer_id="123456789",
        phone="+1234567890",
        usual_size="M",
        height=175,
        weight=70
    )

    # Mock order data
    service.get_order_with_pending_size_confirmation.return_value = MagicMock(
        id=UUID("87654321-4321-8765-4321-876543210987"),
        shopify_order_id="987654321",
        customer_id=UUID("12345678-1234-5678-1234-567812345678"),
        order_number="1001",
        original_size="M",
        confirmed_size=None,
        product_id="product_123",
        product_title="Test Product",
        variant_id="variant_123",
        line_item_id="line_item_123",
        status="pending",
        size_confirmed=False,
        fulfilled=False
    )

    # Mock message data
    service.get_messages_by_order.return_value = []

    return service

@pytest.fixture
def mock_twilio_service():
    service = AsyncMock()
    service.send_whatsapp_message.return_value = None
    service.parse_webhook_request.return_value = {
        "from_phone": "+1234567890",
        "body": "Yes, the size is correct"
    }
    return service

@pytest.fixture
def mock_vertex_ai_service():
    service = AsyncMock()
    service.generate_response.return_value = "Thank you for confirming your size."
    service.detect_intent.return_value = ("CONFIRM", {"preferred_size": "M"})
    return service

@pytest.fixture
def mock_shopify_service():
    service = AsyncMock()
    service.parse_order_data.return_value = (
        {
            "shopify_customer_id": "123456789",
            "phone": "+1234567890",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User"
        },
        {
            "shopify_order_id": "987654321",
            "order_number": "1001",
            "original_size": "M",
            "product_id": "product_123",
            "variant_id": "variant_123",
            "line_item_id": "line_item_123",
            "product_title": "Test Product"
        }
    )
    service.update_order_size.return_value = None
    service.trigger_fulfillment.return_value = None
    return service

@pytest.fixture
def mock_conversation_service():
    service = AsyncMock()
    service.start_conversation.return_value = None
    service.process_customer_reply.return_value = None
    return service

@pytest.fixture
def shopify_webhook_payload():
    return {
        "id": 987654321,
        "order_number": "1001",
        "customer": {
            "id": 123456789,
            "email": "test@example.com",
            "phone": "+1234567890",
            "first_name": "Test",
            "last_name": "User"
        },
        "line_items": [
            {
                "id": "line_item_123",
                "product_id": "product_123",
                "variant_id": "variant_123",
                "title": "Test Product",
                "variant_title": "Medium",
                "properties": [
                    {
                        "name": "Size",
                        "value": "M"
                    }
                ]
            }
        ]
    }

@pytest.fixture
def twilio_webhook_payload():
    return {
        "From": "+1234567890",
        "Body": "Yes, the size is correct",
        "MessageSid": "SM12345678901234567890123456789012",
        "NumMedia": "0"
    }
