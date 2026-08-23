from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict

class SellerCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    display_name: str = Field(min_length=1, max_length=120)
    country: str = Field(pattern=r"^(BD|IN|ZA)$")
    language: str = Field(min_length=2, max_length=20)
    currency: str = Field(pattern=r"^(BDT|INR|ZAR)$")
    payment_provider: str | None = Field(default=None, max_length=40)
    payment_destination: str | None = Field(default=None, max_length=120)
    social_provider: str | None = Field(default=None, max_length=40)
    latitude: Decimal | None = Field(default=None, ge=-90, le=90)
    longitude: Decimal | None = Field(default=None, ge=-180, le=180)

class ProductCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    seller_id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=180)
    description: str | None = Field(default=None, max_length=5000)
    production_cost: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    selling_price: Decimal | None = Field(default=None, gt=0, max_digits=14, decimal_places=2)
    margin_percent: Decimal | None = Field(default=None, ge=0, le=100, max_digits=8, decimal_places=2)
    quantity_available: int = Field(ge=0, le=1000000000)

class OrderCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    seller_id: int = Field(gt=0)
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0, le=1000000000)
    payment_method: str = Field(min_length=1, max_length=30)
    customer_name: str | None = Field(default=None, max_length=120)
    customer_contact: str | None = Field(default=None, max_length=120)
    delivery_address: str | None = Field(default=None, max_length=2000)

class PaymentVerificationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provider_reference: str | None = Field(default=None, max_length=160)
    receipt_present: bool = False

class AgentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    seller_id: int = Field(gt=0)
    message: str = Field(min_length=1, max_length=12000)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    language: str | None = Field(default=None, min_length=2, max_length=20)
    country: str | None = Field(default=None, pattern=r"^(BD|IN|ZA)$")

class FinancialPlanningRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    seller_id: int = Field(gt=0)
    product_id: int | None = Field(default=None, gt=0)
    current_cash: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    expected_income: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    known_obligations: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    inventory_value: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    business_cycle_days: int | None = Field(default=None, ge=1, le=3650)
    disruption_window_days: int | None = Field(default=None, ge=1, le=3650)
    notes: str | None = Field(default=None, max_length=4000)


class SocialStatusRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    seller_id: int = Field(gt=0)


class ActionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    seller_id: int = Field(gt=0)
    action_type: str = Field(min_length=1, max_length=40)
    payload: dict = Field(default_factory=dict)
