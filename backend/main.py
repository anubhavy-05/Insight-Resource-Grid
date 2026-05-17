from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import models, schemas
from database import engine, SessionLocal
import jwt
from datetime import datetime, timedelta, timezone
from typing import List
from fastapi.middleware.cors import CORSMiddleware



# Database table create karna
models.Base.metadata.create_all(bind=engine)

app = FastAPI()
# Ye hamara secret key hai (jaise ek master password). Ise kisi ko nahi batana chahiye!
SECRET_KEY = "my_super_secret_key" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 # Token 30 minute me expire ho jayega


# --- CORS SETUP (Frontend Bridge) ---
# Yahan hum un sabhi frontend ports ko allow kar rahe hain jahan se request aa sakti hai
origins = [
    "http://localhost:3000",      # Agar aap React (CRA) use karenge
    "http://localhost:5173",      # Agar aap React (Vite) use karenge
    "http://127.0.0.1:5500",      # Agar aap normal HTML/JS (VS Code Live Server) use karenge
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,    # Sirf in URLs ko allow karo
    allow_credentials=True,   # Cookies aur Tokens allow karo
    allow_methods=["*"],      # GET, POST, PUT, DELETE sabhi allow karo
    allow_headers=["*"],      # Har tarah ka data (Headers) allow karo
)



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

# --- LOGIN API (Updated for Swagger UI) ---
@app.post("/login/")
def login(user_credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Swagger hamesha 'username' field bhejta hai form me, isliye hum usi ko email maan kar check karenge
    user = db.query(models.User).filter(models.User.email == user_credentials.username).first()
    
    if not user:
        raise HTTPException(status_code=403, detail="Invalid Credentials")
    
    is_password_correct = pwd_context.verify(user_credentials.password, user.hashed_password)
    
    if not is_password_correct:
        raise HTTPException(status_code=403, detail="Invalid Credentials")
    
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    token_data = {
        "sub": user.email, 
        "role": user.role, 
        "exp": expire      
    }
    
    token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}



# Ye Swagger UI ko batayega ki token kahan se lana hai
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# --- SECURITY GUARD (Token Check Karne Wala Function) ---
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        # Token ko khol kar check karo
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        
        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token")
            
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    # Agar token sahi hai, toh database se user nikalo
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        
    return user

# --- PROTECTED ROUTE (Sirf Login wale log yahan aa sakte hain) ---
@app.get("/users/me", response_model=schemas.UserResponse)
def read_user_profile(current_user: models.User = Depends(get_current_user)):
    # Ye route sirf tab chalega jab 'get_current_user' token pass kar dega
    return current_user


# --- ADMIN SECURITY GUARD ---
def get_admin_user(current_user: models.User = Depends(get_current_user)):
    # Agar user ka role admin nahi hai, toh seedha 403 error de do
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized. Admin access only!")
    return current_user


# --- SUBMIT RESOURCE API (Protected Route) ---
@app.post("/resources/", response_model=schemas.ResourceResponse)
def create_resource(
    resource: schemas.ResourceCreate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user) # 🔒 Ye Lock hai!
):
    # Naya resource banana, aur owner_id me us user ki ID daalna jo token laya hai
    new_resource = models.Resource(
        title=resource.title,
        description=resource.description,
        link=resource.link,
        owner_id=current_user.id  # 🔑 Foreign Key Connection
    )
    
    # Database me save karna
    db.add(new_resource)
    db.commit()
    db.refresh(new_resource)
    
    return new_resource


# --- APPROVE RESOURCE API (Admin Only) ---
@app.put("/resources/{resource_id}/approve")
def approve_resource(
    resource_id: int, 
    db: Session = Depends(get_db), 
    admin_user: models.User = Depends(get_admin_user) # 🔒 Ye Naya, zyada strict Lock hai
):
    # 1. Pehle database me resource dhundo
    resource = db.query(models.Resource).filter(models.Resource.id == resource_id).first()
    
    # Agar resource mila hi nahi
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    # 2. Agar mil gaya, toh uska status update kardo
    resource.status = "Approved"
    db.commit()
    db.refresh(resource)
    
    return {"message": "Resource Approved Successfully!", "resource": resource}



# --- GET ALL APPROVED RESOURCES (Public Route) ---
@app.get("/resources/", response_model=List[schemas.ResourceResponse])
def get_approved_resources(db: Session = Depends(get_db)):
    # Database se sirf wo resources nikalo jinka status "Approved" hai
    approved_resources = db.query(models.Resource).filter(models.Resource.status == "Approved").all()
    
    return approved_resources 




# --- DELETE RESOURCE API (Admin Only) ---
@app.delete("/resources/{resource_id}")
def delete_resource(
    resource_id: int, 
    db: Session = Depends(get_db), 
    admin_user: models.User = Depends(get_admin_user) # 🔒 Sirf Admin isko chhu sakta hai
):
    # 1. Database me resource dhundo
    resource = db.query(models.Resource).filter(models.Resource.id == resource_id).first()
    
    # Agar resource nahi mila
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    # 2. Agar mil gaya, toh usko permanently delete kardo
    db.delete(resource)
    db.commit()
    
    return {"message": f"Resource {resource_id} has been permanently deleted."}



# --- GET MY UPLOADS API (Logged-in Users Only) ---
@app.get("/my-uploads/", response_model=List[schemas.ResourceResponse])
def get_my_uploads(
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user) # 🔒 Lock (Sirf logged-in users ke liye)
):
    # Database se sirf wahi resources nikalo jinki owner_id current user ki ID se match karti ho
    my_resources = db.query(models.Resource).filter(models.Resource.owner_id == current_user.id).all()
    
    return my_resources



# --- GET PENDING RESOURCES (Admin Dashboard Ke Liye) ---
@app.get("/admin/resources/pending", response_model=List[schemas.ResourceResponse])
def get_pending_resources(
    db: Session = Depends(get_db), 
    admin_user: models.User = Depends(get_admin_user) # 🔒 Sirf Admin allowed hai
):
    # Database se sirf wo resources nikalo jinka status "Pending" hai
    pending_resources = db.query(models.Resource).filter(models.Resource.status == "Pending").all()
    return pending_resources