from pydantic import BaseModel, EmailStr

# Jab user signup karega toh hume ye data chahiye
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

# Database se data wapas bhejte waqt hum password nahi bhejenge
class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    is_active: bool

    class Config:
        from_attributes = True