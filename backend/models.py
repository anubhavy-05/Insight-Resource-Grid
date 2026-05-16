from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


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
    

    # --- RESOURCE TABLE ---
class Resource(Base):
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    link = Column(String) 
    status = Column(String, default="Pending") # Naya data hamesha pending rahega
    
    # Ye Foreign Key User table ki ID se connect karegi
    owner_id = Column(Integer, ForeignKey("users.id")) 
    
    # Ye relationship hume backend me data fetch karne me madad karegi
    owner = relationship("User")