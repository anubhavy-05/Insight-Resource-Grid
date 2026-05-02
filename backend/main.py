from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import models, schemas
from database import engine, SessionLocal
import jwt
from datetime import datetime, timedelta, timezone

# Database table create karna
models.Base.metadata.create_all(bind=engine)

app = FastAPI()
# Ye hamara secret key hai (jaise ek master password). Ise kisi ko nahi batana chahiye!
SECRET_KEY = "my_super_secret_key" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 # Token 30 minute me expire ho jayega

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

# --- LOGIN API ---
@app.post("/login/")
def login(user_credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    # 1. Database me check karo ki is email se koi user hai ya nahi
    user = db.query(models.User).filter(models.User.email == user_credentials.email).first()
    
    # Agar user nahi mila, toh error do (403 Forbidden)
    if not user:
        raise HTTPException(status_code=403, detail="Invalid Credentials")
    
    # 2. Agar email mil gaya, toh password match karo
    is_password_correct = pwd_context.verify(user_credentials.password, user.hashed_password)
    
    if not is_password_correct:
        raise HTTPException(status_code=403, detail="Invalid Credentials")
    
    # 3. Email aur Password dono sahi hain! Ab "Wristband" (Token) banao
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Payload: Ye wo data hai jo token ke andar chhipa hoga
    token_data = {
        "sub": user.email, # sub ka matlab subject (user ki pehchan)
        "role": user.role, # Yahan pata chalega ki ye 'admin' hai ya 'user'
        "exp": expire      # Expiry time
    }
    
    # Token Generate karna
    token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
    
    return {"access_token": token, "token_type": "bearer"}