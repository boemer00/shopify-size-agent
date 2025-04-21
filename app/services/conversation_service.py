from enum import Enum
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID

from app.services.supabase_service import SupabaseService
from app.services.twilio_service import TwilioService
from app.services.vertex_ai_service import VertexAIService
from app.services.shopify_service import ShopifyService
from app.models.message import MessageCreate
from app.models.order import OrderUpdate
from app.models.conversation import ConversationStatus, ConversationUpdate


class ConversationPhase(str, Enum):
    CONFIRMATION = "CONFIRMATION"  # Initial phase asking if size is correct
    SIZING_QUESTIONS = "SIZING_QUESTIONS"  # Asking about usual size, height, weight
    RECOMMENDATION = "RECOMMENDATION"  # Recommending a size
    COMPLETE = "COMPLETE"  # Conversation is complete


class ConversationService:
    def __init__(self):
        self.supabase_service = SupabaseService()
        self.twilio_service = TwilioService()
        self.vertex_ai_service = VertexAIService()
        self.shopify_service = ShopifyService()
        # For backward compatibility - messenger_service is an alias for twilio_service
        self.messenger_service = self.twilio_service

    async def start_conversation(self, order_id: UUID, customer_id: UUID, phone: str, product_title: str, original_size: str) -> None:
        """
        Start a new conversation with a customer

        Args:
            order_id: The UUID of the order in our database
            customer_id: The UUID of the customer in our database
            phone: The customer's phone number
            product_title: The title of the product
            original_size: The original size ordered
        """
        # Get AI to generate the initial message
        initial_message = await self.vertex_ai_service.generate_response(
            product_title=product_title,
            original_size=original_size,
            conversation_history=[],
            phase=ConversationPhase.CONFIRMATION
        )

        # Send the message via Twilio
        await self.twilio_service.send_whatsapp_message(to_phone=phone, message=initial_message)

        # Save the message to Supabase
        message_create = MessageCreate(
            order_id=order_id,
            customer_id=customer_id,
            direction="outbound",
            content=initial_message,
            conversation_phase=ConversationPhase.CONFIRMATION
        )
        await self.supabase_service.create_message(message_create)

    async def process_customer_reply(self, from_phone: str, message_content: str) -> None:
        """
        Process a reply from a customer

        Args:
            from_phone: The customer's phone number
            message_content: The content of the message
        """
        # Get the customer by phone number
        customer = await self.supabase_service.get_customer_by_phone(from_phone)
        if not customer:
            # No customer found, can't process
            print(f"Customer not found for phone {from_phone}")
            return

        # Get the conversation by phone number
        conversation = await self.get_conversation_by_phone(from_phone)
        if not conversation:
            # No conversation found, can't process
            print(f"No conversation found for phone {from_phone}")
            return

        # Get the most recent order with pending size confirmation
        order = await self.supabase_service.get_order_with_pending_size_confirmation(customer.id)
        if not order:
            # No pending order found
            print(f"No pending order found for customer {customer.id}")
            return

        # Get conversation history
        conversation_history = await self.supabase_service.get_messages_by_order(order.id)
        messages_dict = [msg.dict() for msg in conversation_history]

        # Determine current phase based on last message
        current_phase = ConversationPhase.CONFIRMATION
        if conversation_history:
            last_message = conversation_history[-1]
            current_phase = last_message.conversation_phase or ConversationPhase.CONFIRMATION

        # Detect intent from customer message
        intent, entities = await self.vertex_ai_service.detect_intent(message_content)

        # Save customer message to database
        customer_message = MessageCreate(
            order_id=order.id,
            customer_id=customer.id,
            direction="inbound",
            content=message_content,
            conversation_phase=current_phase,
            intent=intent,
            entities=entities
        )
        await self.supabase_service.create_message(customer_message)

        # Add customer message to conversation history for AI context
        messages_dict.append(customer_message.dict())

        # Update customer info if entities were detected
        customer_update_data = {}
        if entities.get("usual_size"):
            customer_update_data["usual_size"] = entities["usual_size"]
        if entities.get("height"):
            customer_update_data["height"] = entities["height"]
        if entities.get("weight"):
            customer_update_data["weight"] = entities["weight"]

        if customer_update_data:
            await self.supabase_service.update_customer(customer.id, customer_update_data)

        # Determine next phase based on intent
        next_phase = current_phase

        if current_phase == ConversationPhase.CONFIRMATION:
            if intent == "CONFIRM":
                # Customer confirmed size is correct
                next_phase = ConversationPhase.COMPLETE

                # Update the conversation status
                await self.update_conversation_status(conversation.id, ConversationStatus.COMPLETED)

                # Get the recommended size from entities or use original
                new_size = entities.get("preferred_size") or order.original_size

                # Update order in our database
                order_update = OrderUpdate(
                    confirmed_size=new_size,
                    status="confirmed",
                    size_confirmed=True
                )
                await self.supabase_service.update_order(order.id, order_update)

            elif intent in ["UNSURE", "CHANGE_SIZE"]:
                # Customer is unsure or wants to change size
                next_phase = ConversationPhase.SIZING_QUESTIONS
            # Leave as CONFIRMATION for OTHER intent

        elif current_phase == ConversationPhase.SIZING_QUESTIONS:
            # If we have enough information to make a recommendation
            if (entities.get("usual_size") or (entities.get("height") and entities.get("weight"))):
                next_phase = ConversationPhase.RECOMMENDATION

        elif current_phase == ConversationPhase.RECOMMENDATION:
            if intent == "CONFIRM":
                # Customer confirmed the recommendation
                next_phase = ConversationPhase.COMPLETE

                # Update the conversation status
                await self.update_conversation_status(conversation.id, ConversationStatus.COMPLETED)

                # Get the recommended size from entities or use original
                new_size = entities.get("preferred_size") or order.original_size

                # Update order in our database
                order_update = OrderUpdate(
                    confirmed_size=new_size,
                    status="confirmed",
                    size_confirmed=True
                )
                await self.supabase_service.update_order(order.id, order_update)

                # Update order in Shopify
                await self.shopify_service.update_order_size(
                    order_id=order.shopify_order_id,
                    line_item_id=order.line_item_id,
                    new_size=new_size
                )

                # Trigger fulfillment if size is confirmed
                if intent == "CONFIRM":
                    await self.shopify_service.trigger_fulfillment(order.shopify_order_id)

                    # Update order as fulfilled
                    fulfilled_update = OrderUpdate(fulfilled=True)
                    await self.supabase_service.update_order(order.id, fulfilled_update)

        # Generate AI response based on the new phase
        ai_response = await self.vertex_ai_service.generate_response(
            product_title=order.product_title,
            original_size=order.original_size,
            conversation_history=messages_dict,
            phase=next_phase
        )

        # Send the response to the customer
        await self.messenger_service.send_message(to_phone=from_phone, message=ai_response)

        # Save the response to database
        ai_message = MessageCreate(
            order_id=order.id,
            customer_id=customer.id,
            direction="outbound",
            content=ai_response,
            conversation_phase=next_phase
        )
        await self.supabase_service.create_message(ai_message)

    async def get_conversation_by_phone(self, phone_number: str):
        """
        Get a conversation by phone number

        Args:
            phone_number: The phone number to look up

        Returns:
            The conversation if found, None otherwise
        """
        # Query the database for the conversation with the given phone number
        return await self.supabase_service.get_conversation_by_phone(phone_number)

    async def update_conversation_status(self, conversation_id: UUID, status: ConversationStatus) -> None:
        """
        Update the status of a conversation

        Args:
            conversation_id: The UUID of the conversation to update
            status: The new status to set
        """
        update_data = ConversationUpdate(status=status)
        await self.supabase_service.update_conversation(conversation_id, update_data)
