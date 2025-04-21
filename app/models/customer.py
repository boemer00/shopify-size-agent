from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class Customer(BaseModel):
    """
    Model for customer data
    """
    id: UUID
    shopify_customer_id: str  # Changed from int to str to ensure consistent type
    phone: str
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    name: Optional[str] = None  # Combined name field
    usual_size: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        orm_mode = True


class CustomerCreate(BaseModel):
    """
    Model for creating a new customer
    """
    shopify_customer_id: str  # Changed from int to str to ensure consistent type
    phone: str
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    usual_size: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None


class CustomerUpdate(BaseModel):
    """
    Model for updating a customer
    """
    phone: Optional[str] = None
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    usual_size: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
