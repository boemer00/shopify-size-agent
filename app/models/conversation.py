from enum import Enum
from typing import Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class ConversationStatus(str, Enum):
    """
    Enum for conversation status
    """
    AWAITING_SIZE_CONFIRMATION = "awaiting_size_confirmation"
    AWAITING_SIZING_INFO = "awaiting_sizing_info"
    AWAITING_RECOMMENDATION_CONFIRMATION = "awaiting_recommendation_confirmation"
    COMPLETED = "completed"


class Conversation(BaseModel):
    """
    Model for conversation data
    """
    id: UUID
    order_id: UUID
    phone_number: str
    status: ConversationStatus = ConversationStatus.AWAITING_SIZE_CONFIRMATION
    created_at: datetime
    updated_at: datetime


class ConversationCreate(BaseModel):
    """
    Model for creating a new conversation
    """
    order_id: UUID
    phone_number: str
    status: ConversationStatus = ConversationStatus.AWAITING_SIZE_CONFIRMATION


class ConversationUpdate(BaseModel):
    """
    Model for updating a conversation
    """
    status: Optional[ConversationStatus] = None
