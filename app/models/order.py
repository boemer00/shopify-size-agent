from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class Order(BaseModel):
    """
    Model for order data
    """
    id: UUID
    shopify_order_id: str  # Changed from int to str to ensure consistent type
    customer_id: UUID
    order_number: str
    original_size: str
    confirmed_size: Optional[str] = None
    product_id: str  # Changed from int to str
    variant_id: str  # Changed from int to str
    line_item_id: str  # Changed from int to str
    product_title: str
    status: str = "pending"
    fulfilled: bool = False
    size_confirmed: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        orm_mode = True


class OrderCreate(BaseModel):
    """
    Model for creating a new order
    """
    shopify_order_id: str  # Changed from int to str
    customer_id: UUID
    order_number: str
    original_size: str
    product_id: str  # Changed from int to str
    variant_id: str  # Changed from int to str
    line_item_id: str  # Changed from int to str
    product_title: str


class OrderUpdate(BaseModel):
    """
    Model for updating an order
    """
    confirmed_size: Optional[str] = None
    status: Optional[str] = None
    fulfilled: Optional[bool] = None
    size_confirmed: Optional[bool] = None
