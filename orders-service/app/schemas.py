from pydantic import BaseModel, Field
from typing import List

class OrderItem(BaseModel):
    sku: str
    qty: int

class CreateOrderRequest(BaseModel):
    customer_id: str
    items: List[OrderItem]

class AcceptedResponse(BaseModel):
    request_id: str = Field(..., description="Idempotency key hash")
    message: str = "Enqueued"

class CreatedOrderResponse(BaseModel):
    order_id: str
    status: str = "CREATED"
