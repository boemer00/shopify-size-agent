from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal
from datetime import datetime
from uuid import UUID


class Message(BaseModel):
    id: Optional[UUID] = None
    order_id: UUID
    customer_id: UUID
    direction: Literal["inbound", "outbound"]
    content: str
    media_url: Optional[str] = None
    conversation_phase: Optional[str] = None
    intent: Optional[str] = None
    entities: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class MessageCreate(BaseModel):
    order_id: UUID
    customer_id: UUID
    direction: Literal["inbound", "outbound"]
    content: str
    media_url: Optional[str] = None
    conversation_phase: Optional[str] = None
    intent: Optional[str] = None
    entities: Optional[Dict[str, Any]] = None
