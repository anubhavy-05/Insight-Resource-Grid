# main.py — line-by-line explanation

Below are concise explanations for each line (and small groups of closely related lines) from `backend/main.py` so you can understand what the app does and why each part is present.

```python
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
origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_pwd = pwd_context.hash(user.password)
    new_user = models.User(
        name=user.name, 
        email=user.email, 
        hashed_password=hashed_pwd
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# --- LOGIN API (Updated for Swagger UI) ---
@app.post("/login/")
def login(user_credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == user_credentials.username).first()
    if not user:
        raise HTTPException(status_code=403, detail="Invalid Credentials")
    is_password_correct = pwd_context.verify(user_credentials.password, user.hashed_password)
    if not is_password_correct:
        raise HTTPException(status_code=403, detail="Invalid Credentials")
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token_data = {"sub": user.email, "role": user.role, "exp": expire}
    token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}


# Ye Swagger UI ko batayega ki token kahan se lana hai
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# --- SECURITY GUARD (Token Check Karne Wala Function) ---
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

@app.get("/users/me", response_model=schemas.UserResponse)
def read_user_profile(current_user: models.User = Depends(get_current_user)):
    return current_user


# --- ADMIN SECURITY GUARD ---
def get_admin_user(current_user: models.User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized. Admin access only!")
    return current_user


# --- SUBMIT RESOURCE API (Protected Route) ---
@app.post("/resources/", response_model=schemas.ResourceResponse)
def create_resource(
    resource: schemas.ResourceCreate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    new_resource = models.Resource(
        title=resource.title,
        description=resource.description,
        link=resource.link,
        owner_id=current_user.id
    )
    db.add(new_resource)
    db.commit()
    db.refresh(new_resource)
    return new_resource


# --- APPROVE RESOURCE API (Admin Only) ---
@app.put("/resources/{resource_id}/approve")
def approve_resource(
    resource_id: int, 
    db: Session = Depends(get_db), 
    admin_user: models.User = Depends(get_admin_user)
):
    resource = db.query(models.Resource).filter(models.Resource.id == resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    resource.status = "Approved"
    db.commit()
    db.refresh(resource)
    return {"message": "Resource Approved Successfully!", "resource": resource}


# --- GET ALL APPROVED RESOURCES (Public Route) ---
@app.get("/resources/", response_model=List[schemas.ResourceResponse])
def get_approved_resources(db: Session = Depends(get_db)):
    approved_resources = db.query(models.Resource).filter(models.Resource.status == "Approved").all()
    return approved_resources


# --- DELETE RESOURCE API (Admin Only) ---
@app.delete("/resources/{resource_id}")
def delete_resource(
    resource_id: int, 
    db: Session = Depends(get_db), 
    admin_user: models.User = Depends(get_admin_user)
):
    resource = db.query(models.Resource).filter(models.Resource.id == resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    db.delete(resource)
    db.commit()
    return {"message": f"Resource {resource_id} has been permanently deleted."}


# --- GET MY UPLOADS API (Logged-in Users Only) ---
@app.get("/my-uploads/", response_model=List[schemas.ResourceResponse])
def get_my_uploads(
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    my_resources = db.query(models.Resource).filter(models.Resource.owner_id == current_user.id).all()
    return my_resources


# --- GET PENDING RESOURCES (Admin Dashboard Ke Liye) ---
@app.get("/admin/resources/pending", response_model=List[schemas.ResourceResponse])
def get_pending_resources(
    db: Session = Depends(get_db), 
    admin_user: models.User = Depends(get_admin_user)
):
    pending_resources = db.query(models.Resource).filter(models.Resource.status == "Pending").all()
    return pending_resources
```

Explanations (by line/group):

1-3: `from fastapi import FastAPI, Depends, HTTPException, status`
- Import core FastAPI pieces. `FastAPI()` creates the app; `Depends` is for dependency injection; `HTTPException` is used to send errors; `status` has HTTP status constants.

4: `from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm`
- `OAuth2PasswordBearer` tells FastAPI where to get the token (used by Swagger UI); `OAuth2PasswordRequestForm` parses the login form that Swagger sends (it uses `username`/`password`).

5: `from sqlalchemy.orm import Session`
- Import SQLAlchemy's `Session` type used for type hints and dependency injection.

6: `from passlib.context import CryptContext`
- Import Passlib helper to hash & verify passwords securely (bcrypt here).

7: `import models, schemas`
- Import your ORM models and Pydantic schemas. `models` has SQLAlchemy classes; `schemas` defines request/response shapes.

8: `from database import engine, SessionLocal`
- Import the `engine` and `SessionLocal` created in `database.py` — used to create tables and sessions.

9: `import jwt`
- Import PyJWT (or compatible library) for encoding/decoding JSON Web Tokens.

10: `from datetime import datetime, timedelta, timezone`
- For setting token expiration times in UTC.

11: `from typing import List`
- For response type hints (list of resources).

12: `from fastapi.middleware.cors import CORSMiddleware`
- Import middleware to allow cross-origin requests from the frontend.

14: `models.Base.metadata.create_all(bind=engine)`
- Create DB tables defined in `models` if they do not already exist. Use in development; production should use migrations.

16: `app = FastAPI()`
- Instantiate the FastAPI application — the central app object.

17-19: SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
- `SECRET_KEY`: symmetric key used to sign JWTs (keep secret). `ALGORITHM` specifies the HMAC algorithm. `ACCESS_TOKEN_EXPIRE_MINUTES` controls token lifetime.

22-31: CORS `origins` list and `app.add_middleware(...)`
- Define allowed frontend origins and add `CORSMiddleware` so browser frontends can call the API. `allow_origins` restricts where requests can come from; `allow_credentials=True` allows cookies/authorization headers.

36: `pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")`
- Create a password-hashing context. `bcrypt` is used for secure hashing; `deprecated="auto"` helps with algorithm upgrades.

39-44: `def get_db(): ...`
- Dependency that yields a DB session. It opens a `SessionLocal()` and `finally` ensures the session is closed, preventing connection leaks. Use as `db: Session = Depends(get_db)` in routes.

46-48: `@app.get("/") def home(): ...`
- Simple health-check endpoint returning a JSON message to confirm the backend is running.

51-68: `create_user` endpoint
- Validates if email already exists, hashes the password, creates `models.User`, adds and commits to DB, refreshes the instance (load defaults/ids), and returns new user. Important points:
  - `response_model=schemas.UserResponse` makes FastAPI return only fields defined in that schema.
  - `db.refresh(new_user)` populates auto-generated fields like `id` after commit.

70-86: `login` endpoint
- Accepts a form (`OAuth2PasswordRequestForm`) where Swagger sends `username` and `password`. Steps:
  - Lookup user by email (treating `username` as email). If not found, raise 403.
  - Verify password using `pwd_context.verify`.
  - Create `expire` datetime and assemble `token_data` with `sub` (subject/email), `role`, and `exp`.
  - `jwt.encode(...)` returns a signed token string returned to client.

89: `oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")`
- Tells FastAPI's OpenAPI/Swagger that the token is obtained from the `/login` endpoint. It also provides a dependency that reads the `Authorization: Bearer <token>` header.

92-110: `get_current_user` function
- Dependency that decodes token and returns the authenticated `models.User`:
  - `jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])` verifies signature and checks `exp`.
  - If token missing `sub` or invalid/expired, raise 401 with appropriate message.
  - If token valid, fetch user from DB; if not found raise 401.
  - Returns `user` model instance for downstream routes.

112-114: `@app.get("/users/me")` route
- Protected route that simply returns the current user's data (via dependency injection using `get_current_user`). The `response_model` enforces the response shape.

118-122: `get_admin_user` guard
- Ensures the current user has `role == "admin"`; otherwise raises 403. Use this as a dependency on admin-only routes.

125-147: `create_resource` endpoint
- Protected route that creates a `models.Resource` using `resource` payload and sets `owner_id` to `current_user.id` (owner association). Saves and returns the new resource.

150-165: `approve_resource` endpoint
- Admin-only endpoint that finds a resource by `resource_id`, updates its `status` to "Approved", commits and returns confirmation. Handles `404` if missing.

168-174: `get_approved_resources` endpoint
- Public endpoint that queries only resources with `status == "Approved"` and returns them as a list.

178-190: `delete_resource` endpoint
- Admin-only endpoint that finds a resource by ID, deletes it, commits, and returns a message. Raises `404` if not found.

194-200: `get_my_uploads` endpoint
- Protected endpoint returning resources where `owner_id` equals the current user's `id`.

203-207: `get_pending_resources` endpoint
- Admin-only endpoint returning resources with `status == "Pending"` for an admin dashboard/review workflow.

Practical tips & pitfalls:
- Always keep `SECRET_KEY` secret. For development it's okay to hardcode; in production load from env vars or a secrets manager.
- Use HTTPS in production to protect tokens in transit.
- Consider token revocation (blacklist) if you need to invalidate tokens before expiration.
- Use Alembic for schema migrations instead of `create_all()` in production.
- Close DB sessions to avoid leaking connections; the `get_db` dependency pattern shown is correct.
- Validate and sanitize inputs in `schemas` to avoid unexpected DB state.

Next step: I can (a) add example frontend requests, (b) add transaction/rollback handling to critical endpoints, or (c) update README with run instructions — tell me which you'd like.
