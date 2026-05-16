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
        
class UserLogin(BaseModel):
    email: EmailStr
    password: str


    # --- RESOURCE SCHEMAS ---

# Jab user data bhejega (Upload karte waqt)
class ResourceCreate(BaseModel):
    title: str
    description: str
    link: str

# Jab backend se data wapas aayega (Response me)
class ResourceResponse(BaseModel):
    id: int
    title: str
    description: str
    link: str
    status: str
    owner_id: int

    class Config:
        from_attributes = True