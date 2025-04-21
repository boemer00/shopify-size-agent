import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from uuid import UUID
import os
from datetime import datetime

from app.services.conversation_service import ConversationService, ConversationPhase
from app.models.message import MessageCreate
from app.models.conversation import Conversation, ConversationStatus

@pytest.fixture
def conversation_service(mock_supabase_service, mock_twilio_service, mock_vertex_ai_service, mock_shopify_service):
    # Make sure testing flag is set
    os.environ["TESTING"] = "true"

    service = ConversationService()
    service.supabase_service = mock_supabase_service
    service.twilio_service = mock_twilio_service
    service.vertex_ai_service = mock_vertex_ai_service
    service.shopify_service = mock_shopify_service
    return service

class TestConversationService:

    async def test_start_conversation(self, conversation_service):
        """Test starting a new conversation"""
        # Setup test data
        order_id = UUID("87654321-4321-8765-4321-876543210987")
        customer_id = UUID("12345678-1234-5678-1234-567812345678")
        phone = "+1234567890"
        product_title = "Test Product"
        original_size = "M"

        # Mock AI response
        conversation_service.vertex_ai_service.generate_response.return_value = "Hi! We noticed you ordered a Test Product in size M. Is this the correct size for you?"

        # Call the method
        await conversation_service.start_conversation(
            order_id=order_id,
            customer_id=customer_id,
            phone=phone,
            product_title=product_title,
            original_size=original_size
        )

        # Verify the AI service was called correctly
        conversation_service.vertex_ai_service.generate_response.assert_called_once_with(
            product_title=product_title,
            original_size=original_size,
            conversation_history=[],
            phase=ConversationPhase.CONFIRMATION
        )

        # Verify the Twilio service was called correctly
        conversation_service.twilio_service.send_whatsapp_message.assert_called_once_with(
            to_phone=phone,
            message="Hi! We noticed you ordered a Test Product in size M. Is this the correct size for you?"
        )

        # Verify the message was saved to the database
        conversation_service.supabase_service.create_message.assert_called_once()
        call_args = conversation_service.supabase_service.create_message.call_args[0][0]
        assert isinstance(call_args, MessageCreate)
        assert call_args.order_id == order_id
        assert call_args.customer_id == customer_id
        assert call_args.direction == "outbound"
        assert call_args.conversation_phase == ConversationPhase.CONFIRMATION

    async def test_process_customer_reply_confirmation_yes(self, conversation_service):
        """Test processing a 'yes' confirmation from a customer"""
        order_id = UUID("12345678-1234-5678-1234-567812345678")
        phone_number = "+12345678901"
        message_body = "Yes"

        # Set up the mock conversation and order
        conversation = Conversation(
            id=UUID("87654321-8765-4321-8765-432187654321"),
            order_id=order_id,
            phone_number=phone_number,
            status=ConversationStatus.AWAITING_SIZE_CONFIRMATION,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        conversation_service.get_conversation_by_phone = AsyncMock(return_value=conversation)
        conversation_service.supabase_service.get_order = AsyncMock(return_value=MagicMock(
            id=order_id,
            confirmed_size="L"
        ))
        conversation_service.update_conversation_status = AsyncMock()
        conversation_service.supabase_service.update_order = AsyncMock()
        conversation_service.messenger_service.send_message = AsyncMock()

        await conversation_service.process_customer_reply(phone_number, message_body)

        # Assert that the conversation status was updated
        conversation_service.update_conversation_status.assert_called_once_with(
            conversation.id, ConversationStatus.COMPLETED
        )

        # Assert that the order was updated
        conversation_service.supabase_service.update_order.assert_called_once()

        # Assert that the confirmation message was sent
        conversation_service.messenger_service.send_message.assert_called_once()

    async def test_process_customer_reply_unsure(self, conversation_service):
        """Test processing an 'unsure' reply to the confirmation phase"""
        # Setup
        from_phone = "+1234567890"
        message_content = "I'm not sure, I usually wear L"

        # Mock intent detection
        conversation_service.vertex_ai_service.detect_intent.return_value = ("UNSURE", {"usual_size": "L"})

        # Mock conversation history
        previous_message = MagicMock(conversation_phase=ConversationPhase.CONFIRMATION)
        conversation_service.supabase_service.get_messages_by_order.return_value = [previous_message]

        # Call the method
        await conversation_service.process_customer_reply(
            from_phone=from_phone,
            message_content=message_content
        )

        # Verify outbound message was in SIZING_QUESTIONS phase
        assert conversation_service.supabase_service.create_message.call_count == 2  # Inbound & outbound
        outbound_call = conversation_service.supabase_service.create_message.call_args_list[1][0][0]
        assert outbound_call.conversation_phase == ConversationPhase.SIZING_QUESTIONS

        # Verify customer info was updated
        conversation_service.supabase_service.update_customer.assert_called_with(
            conversation_service.supabase_service.get_customer_by_phone.return_value.id,
            {"usual_size": "L"}
        )

    async def test_process_customer_reply_sizing_to_recommendation(self, conversation_service):
        """Test transition from sizing questions to recommendation phase"""
        # Setup
        from_phone = "+1234567890"
        message_content = "I'm 180cm tall and weigh 80kg"

        # Mock intent detection
        conversation_service.vertex_ai_service.detect_intent.return_value = (
            "PROVIDE_INFO",
            {"height": "180", "weight": "80"}
        )

        # Mock conversation history
        previous_message = MagicMock(conversation_phase=ConversationPhase.SIZING_QUESTIONS)
        conversation_service.supabase_service.get_messages_by_order.return_value = [previous_message]

        # Call the method
        await conversation_service.process_customer_reply(
            from_phone=from_phone,
            message_content=message_content
        )

        # Verify outbound message was in RECOMMENDATION phase
        assert conversation_service.supabase_service.create_message.call_count == 2  # Inbound & outbound
        outbound_call = conversation_service.supabase_service.create_message.call_args_list[1][0][0]
        assert outbound_call.conversation_phase == ConversationPhase.RECOMMENDATION

        # Verify customer info was updated
        conversation_service.supabase_service.update_customer.assert_called_with(
            conversation_service.supabase_service.get_customer_by_phone.return_value.id,
            {"height": "180", "weight": "80"}
        )

    async def test_process_customer_reply_recommendation_confirm(self, conversation_service):
        """Test confirming a size recommendation"""
        # Setup
        from_phone = "+1234567890"
        message_content = "Yes, L sounds good"

        # Mock intent detection
        conversation_service.vertex_ai_service.detect_intent.return_value = ("CONFIRM", {"preferred_size": "L"})

        # Mock conversation history
        previous_message = MagicMock(conversation_phase=ConversationPhase.RECOMMENDATION)
        conversation_service.supabase_service.get_messages_by_order.return_value = [previous_message]

        # Call the method
        await conversation_service.process_customer_reply(
            from_phone=from_phone,
            message_content=message_content
        )

        # Verify outbound message was in COMPLETE phase
        assert conversation_service.supabase_service.create_message.call_count == 2  # Inbound & outbound
        outbound_call = conversation_service.supabase_service.create_message.call_args_list[1][0][0]
        assert outbound_call.conversation_phase == ConversationPhase.COMPLETE

        # Verify order was updated with new size
        order_update_call = conversation_service.supabase_service.update_order.call_args_list[0][0][1]
        assert order_update_call.confirmed_size == "L"
        assert order_update_call.status == "confirmed"
        assert order_update_call.size_confirmed is True

        # Verify Shopify order was updated and fulfillment triggered
        conversation_service.shopify_service.update_order_size.assert_called()
        conversation_service.shopify_service.trigger_fulfillment.assert_called()

    async def test_process_customer_reply_no_customer(self, conversation_service):
        """Test handling a message from an unknown customer"""
        # Setup
        from_phone = "+9999999999"  # Unknown number
        message_content = "Hello, who is this?"

        # Mock customer lookup to return None
        conversation_service.supabase_service.get_customer_by_phone.return_value = None

        # Call the method
        await conversation_service.process_customer_reply(
            from_phone=from_phone,
            message_content=message_content
        )

        # Verify no further processing happened
        conversation_service.supabase_service.get_order_with_pending_size_confirmation.assert_not_called()
        conversation_service.vertex_ai_service.detect_intent.assert_not_called()
        conversation_service.supabase_service.create_message.assert_not_called()

    async def test_process_customer_reply_no_pending_order(self, conversation_service):
        """Test handling a message from a customer with no pending orders"""
        # Setup
        from_phone = "+1234567890"
        message_content = "Hello, is my order ready?"

        # Mock order lookup to return None
        conversation_service.supabase_service.get_order_with_pending_size_confirmation.return_value = None

        # Call the method
        await conversation_service.process_customer_reply(
            from_phone=from_phone,
            message_content=message_content
        )

        # Verify no further processing happened
        conversation_service.vertex_ai_service.detect_intent.assert_not_called()
        conversation_service.supabase_service.create_message.assert_not_called()
