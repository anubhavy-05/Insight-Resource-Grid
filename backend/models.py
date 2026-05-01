from sqlalchemy import Column, Integer, String, Boolean
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    
    # Yahi column decide karega ki kaun admin hai aur kaun nahi
    role = Column(String, default="user") # Default sab "user" honge
    
    is_active = Column(Boolean, default=True)