from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import models, schemas
from database import engine, SessionLocal

# Database table create karna
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Password Hash karne ka setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Database ka Session lene ka function
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def home():
    return {"message": "Insight-Resource-Grid Backend is Live!"}

# Naya route User create karne ke liye
@app.post("/users/", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Pehle check karo ki email pehle se exist toh nahi karta
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Password ko secure hash me badalna
    hashed_pwd = pwd_context.hash(user.password)
    
    # Naya user banana (default role 'user' hoga)
    new_user = models.User(
        name=user.name, 
        email=user.email, 
        hashed_password=hashed_pwd
    )
    
    # Database me save karna
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user