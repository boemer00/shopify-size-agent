import os
import json
from typing import Dict, List, Optional, Any, Tuple

# Only import Google Cloud libraries if not in testing mode
TESTING = os.environ.get("TESTING", "").lower() == "true"
if not TESTING:
    try:
        from google.cloud import aiplatform
        from vertexai.preview.language_models import ChatModel, InputOutputTextPair
    except ImportError:
        print("Warning: Google Cloud libraries not available, AI features will be disabled")

# Constants for prompts
SIZE_CONFIRMATION_PROMPT = """
You are a helpful sizing assistant for a clothing store. Your job is to confirm if the customer's order size is correct.

ORDER INFORMATION:
- Product: {product_title}
- Size ordered: {original_size}

INTERACTION GUIDELINES:
1. Be friendly, brief, and conversational
2. Always start by confirming their purchase and asking about the size
3. If they're unsure about their size, ask helpful questions about:
   - Their usual size at common retailers (Zara, H&M)
   - Their height and weight
4. Make a sizing recommendation based on their responses

CURRENT CONVERSATION PHASE: {phase}
CONVERSATION HISTORY:
{conversation_history}

Respond only with your next message to the customer. Keep it friendly, helpful, and concise.
"""

INTENT_DETECTION_PROMPT = """
Analyze the customer's message below and extract:
1. Their main intent (CONFIRM, UNSURE, CHANGE_SIZE, OTHER)
2. Any key information like usual sizes, height, weight, or preferred size

Customer message: "{message}"

Respond in valid JSON format ONLY, like this:
{
  "intent": "INTENT_TYPE",
  "entities": {
    "usual_size": "Value if mentioned",
    "height": "Value if mentioned",
    "weight": "Value if mentioned",
    "preferred_size": "Value if mentioned"
  }
}
"""


class VertexAIService:
    def __init__(self):
        # Check if we're in testing mode
        self.testing = TESTING

        self.project_id = os.environ.get("VERTEX_AI_PROJECT_ID")
        self.location = os.environ.get("VERTEX_AI_LOCATION", "us-central1")
        self.model_name = "chat-bison"

        # Initialize Vertex AI only if not in testing mode
        if not self.testing:
            try:
                aiplatform.init(project=self.project_id, location=self.location)
                # Load the chat model
                self.chat_model = ChatModel.from_pretrained(self.model_name)
            except Exception as e:
                print(f"Warning: Could not initialize Vertex AI: {e}")
                self.chat_model = None
        else:
            self.chat_model = None

    async def generate_response(
        self,
        product_title: str,
        original_size: str,
        conversation_history: List[Dict[str, str]],
        phase: str = "CONFIRMATION"
    ) -> str:
        """
        Generate a response from the AI model for the size confirmation conversation

        Args:
            product_title: The title of the product
            original_size: The original size ordered
            conversation_history: List of previous messages in the conversation
            phase: The current phase of the conversation

        Returns:
            The model's response
        """
        # Return mock responses in testing mode
        if self.testing:
            responses = {
                "CONFIRMATION": f"Hi! We noticed you ordered a {product_title} in size {original_size}. Is this the correct size for you?",
                "SIZING_QUESTIONS": "What's your usual size at stores like Zara or H&M? Also, could you share your height and weight to help me recommend the best size?",
                "RECOMMENDATION": f"Based on what you've shared, I think size {'L' if original_size == 'M' else 'M'} would be a better fit for you. Would you like me to update your order to that size?",
                "COMPLETE": "Thank you for confirming! Your order has been updated and will be shipped soon. Enjoy your new item!"
            }
            return responses.get(phase, "I'm here to help with your order. How can I assist you?")

        if not self.chat_model:
            return "Sorry, I'm currently unable to process your request. Please contact customer support."

        # Format conversation history
        formatted_history = ""
        for msg in conversation_history:
            role = "Assistant" if msg["direction"] == "outbound" else "Customer"
            formatted_history += f"{role}: {msg['content']}\n"

        # Prepare the prompt
        prompt = SIZE_CONFIRMATION_PROMPT.format(
            product_title=product_title,
            original_size=original_size,
            conversation_history=formatted_history,
            phase=phase
        )

        try:
            # Generate response
            response = self.chat_model.predict(prompt=prompt, temperature=0.2, max_output_tokens=256)
            return response.text
        except Exception as e:
            print(f"Error generating AI response: {e}")
            return "I'm sorry, I'm having trouble processing your request right now. Could you please try again?"

    async def detect_intent(self, message: str) -> Tuple[str, Dict[str, Any]]:
        """
        Detect intent and extract entities from a customer message

        Args:
            message: The customer's message

        Returns:
            Tuple of (intent, entities)
        """
        # Mock intent detection in testing mode
        if self.testing:
            # Simple rules for testing mode
            message = message.lower()
            if "yes" in message or "good" in message or "correct" in message or "perfect" in message:
                return "CONFIRM", {"preferred_size": "M"}
            elif "no" in message or "wrong" in message or "too small" in message or "too big" in message:
                return "CHANGE_SIZE", {"preferred_size": "L" if "big" in message else "S"}
            elif "not sure" in message or "usually" in message or "normally" in message:
                return "UNSURE", {"usual_size": "L" if "large" in message else "M"}
            elif any(unit in message for unit in ["cm", "kg", "ft", "lb"]):
                entities = {}
                if any(h in message for h in ["height", "tall", "cm", "ft", "foot", "feet"]):
                    entities["height"] = "180" if "180" in message else "170"
                if any(w in message for w in ["weight", "kg", "lb", "pound"]):
                    entities["weight"] = "80" if "80" in message else "70"
                return "PROVIDE_INFO", entities
            else:
                return "OTHER", {}

        if not self.chat_model:
            return "OTHER", {}

        prompt = INTENT_DETECTION_PROMPT.format(message=message)

        try:
            # Generate response with intent analysis
            response = self.chat_model.predict(prompt=prompt, temperature=0.1, max_output_tokens=512)

            try:
                # Parse the JSON response
                result = json.loads(response.text)
                intent = result.get("intent", "OTHER")
                entities = result.get("entities", {})
                return intent, entities
            except json.JSONDecodeError:
                # Fallback for parsing errors
                return "OTHER", {}
        except Exception as e:
            print(f"Error detecting intent: {e}")
            return "OTHER", {}
