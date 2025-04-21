import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import os

from app.services.vertex_ai_service import VertexAIService
from app.services.conversation_service import ConversationPhase

class TestVertexAIService:

    @pytest.fixture
    def vertex_ai_service(self):
        # Make sure testing flag is set
        os.environ["TESTING"] = "true"
        service = VertexAIService()
        return service

    @pytest.fixture
    def mock_vertex_client(self):
        with patch("app.services.vertex_ai_service.vertexai") as mock_vertexai:
            mock_client = MagicMock()
            mock_vertexai.init.return_value = None
            mock_vertexai.preview.language_models.ChatModel.from_pretrained.return_value = mock_client

            # Mock chat response
            mock_chat = MagicMock()
            mock_client.start_chat.return_value = mock_chat
            mock_chat.send_message.return_value = MagicMock(text="This is a response from the AI")

            yield mock_client

    async def test_generate_response_confirmation_phase(self, vertex_ai_service):
        """Test generating a response in the confirmation phase"""
        product_title = "Test T-Shirt"
        original_size = "M"
        conversation_history = []
        phase = ConversationPhase.CONFIRMATION

        # Call method
        response = await vertex_ai_service.generate_response(
            product_title=product_title,
            original_size=original_size,
            conversation_history=conversation_history,
            phase=phase
        )

        # Verify response
        assert "Hi! We noticed you ordered a Test T-Shirt in size M" in response
        assert "Is this the correct size for you?" in response

    async def test_generate_response_sizing_questions_phase(self, vertex_ai_service):
        """Test generating a response in the sizing questions phase"""
        product_title = "Test T-Shirt"
        original_size = "M"
        conversation_history = [
            {"direction": "outbound", "content": "Hi! We noticed you ordered a Test T-Shirt in size M. Is this the correct size for you?"},
            {"direction": "inbound", "content": "I'm not sure, I usually wear L"}
        ]
        phase = ConversationPhase.SIZING_QUESTIONS

        # Call method
        response = await vertex_ai_service.generate_response(
            product_title=product_title,
            original_size=original_size,
            conversation_history=conversation_history,
            phase=phase
        )

        # Verify response
        assert "usual size" in response.lower()
        assert "height" in response.lower() or "weight" in response.lower()

    async def test_generate_response_recommendation_phase(self, vertex_ai_service):
        """Test generating a response in the recommendation phase"""
        product_title = "Test T-Shirt"
        original_size = "M"
        conversation_history = [
            {"direction": "outbound", "content": "Hi! We noticed you ordered a Test T-Shirt in size M. Is this the correct size for you?"},
            {"direction": "inbound", "content": "I'm not sure, I usually wear L"},
            {"direction": "outbound", "content": "What's your usual size at other stores?"},
            {"direction": "inbound", "content": "I'm 180cm tall and weigh 80kg"}
        ]
        phase = ConversationPhase.RECOMMENDATION

        # Call method
        response = await vertex_ai_service.generate_response(
            product_title=product_title,
            original_size=original_size,
            conversation_history=conversation_history,
            phase=phase
        )

        # Verify response
        assert "based on what you've shared" in response.lower()
        assert "would be a better fit" in response.lower()

    async def test_generate_response_complete_phase(self, vertex_ai_service):
        """Test generating a response in the complete phase"""
        product_title = "Test T-Shirt"
        original_size = "M"
        conversation_history = [
            {"direction": "outbound", "content": "Hi! We noticed you ordered a Test T-Shirt in size M. Is this the correct size for you?"},
            {"direction": "inbound", "content": "I'm not sure, I usually wear L"},
            {"direction": "outbound", "content": "Based on your info, I recommend size L. Would you like to change your order?"},
            {"direction": "inbound", "content": "Yes, L sounds good"}
        ]
        phase = ConversationPhase.COMPLETE

        # Call method
        response = await vertex_ai_service.generate_response(
            product_title=product_title,
            original_size=original_size,
            conversation_history=conversation_history,
            phase=phase
        )

        # Verify response
        assert "thank you" in response.lower()
        assert "updated" in response.lower() or "changed" in response.lower()

    async def test_detect_intent(self, vertex_ai_service):
        """Test detecting intent from customer message"""
        # Setup message
        message = "Yes, Medium is perfect for me"

        # Call method
        intent, entities = await vertex_ai_service.detect_intent(message)

        # Verify response
        assert intent == "CONFIRM"
        assert "preferred_size" in entities

    async def test_detect_intent_change_size(self, vertex_ai_service):
        """Test detecting intent to change size"""
        # Setup message
        message = "No, it's too small, I need a larger size"

        # Call method
        intent, entities = await vertex_ai_service.detect_intent(message)

        # Verify response
        assert intent == "CHANGE_SIZE"
        assert "preferred_size" in entities

    async def test_detect_intent_provide_measurements(self, vertex_ai_service):
        """Test detecting intent with height and weight"""
        # Setup message
        message = "I am 180cm tall and weigh 80kg"

        # Call method
        intent, entities = await vertex_ai_service.detect_intent(message)

        # Verify response
        assert intent == "PROVIDE_INFO"
        assert "height" in entities
        assert "weight" in entities
