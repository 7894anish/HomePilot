"""All Pydantic request models."""
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


class RegisterIn(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=6)
    phone: Optional[str] = None
    role: Optional[str] = "customer"


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class ForgotIn(BaseModel):
    email: EmailStr


class ResetIn(BaseModel):
    token: str
    password: str = Field(min_length=6)


class ChangePwIn(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6)


class ProfileIn(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    skills: Optional[List[str]] = None


class CategoryIn(BaseModel):
    name: str
    slug: str
    icon: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None


class ServiceIn(BaseModel):
    name: str
    category_id: str
    description: str
    price: float
    duration_minutes: int = 60
    image_url: Optional[str] = None
    features: List[str] = []
    active: bool = True


class CityIn(BaseModel):
    name: str
    state: Optional[str] = None
    active: bool = True


class CouponIn(BaseModel):
    code: str
    discount_percent: float
    max_discount: Optional[float] = None
    min_order: float = 0
    valid_until: Optional[str] = None
    active: bool = True


class BookingCreate(BaseModel):
    service_id: str
    scheduled_date: str
    scheduled_time: str
    address: str
    city: str
    problem_description: str
    images: List[str] = []
    coupon_code: Optional[str] = None
    payment_method: str = "cash"


class BookingStatusIn(BaseModel):
    status: str
    note: Optional[str] = None


class AssignTechIn(BaseModel):
    technician_id: str


class ReviewIn(BaseModel):
    booking_id: str
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = None


class ContactIn(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    subject: str
    message: str


class CheckoutIn(BaseModel):
    booking_id: str
    origin_url: str
