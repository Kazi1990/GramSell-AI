from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session
from ..auth import get_seller, hash_password, issue_token, verify_password
from ..database import get_db
from ..models import Seller

router = APIRouter()

class RegisterRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=120)
    email: str
    password: str = Field(min_length=10, max_length=128)
    country: str = Field(min_length=2, max_length=2)
    language: str = Field(min_length=2, max_length=20)
    currency: str = Field(min_length=3, max_length=3)

    @field_validator("email")
    @classmethod
    def valid_email(cls, value: str) -> str:
        value = value.strip().lower()
        if "@" not in value or "." not in value.rsplit("@", 1)[-1]:
            raise ValueError("Invalid email address")
        return value

class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def valid_email(cls, value: str) -> str:
        value = value.strip().lower()
        if "@" not in value or "." not in value.rsplit("@", 1)[-1]:
            raise ValueError("Invalid email address")
        return value

@router.post('/register')
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    email = payload.email.lower().strip()
    if get_seller(db, email):
        raise HTTPException(status_code=409, detail='Account already exists.')
    seller = Seller(
        display_name=payload.display_name.strip(), email=email,
        password_hash=hash_password(payload.password), country=payload.country.upper(),
        language=payload.language, currency=payload.currency.upper(),
    )
    db.add(seller)
    db.commit()
    db.refresh(seller)
    return {'access_token': issue_token(seller), 'token_type': 'bearer', 'seller_id': seller.id}

@router.post('/login')
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    seller = get_seller(db, payload.email)
    if not seller or not verify_password(payload.password, seller.password_hash):
        raise HTTPException(status_code=401, detail='Invalid credentials.')
    return {'access_token': issue_token(seller), 'token_type': 'bearer', 'seller_id': seller.id}
