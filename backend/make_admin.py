from database import SessionLocal
import models

# Database ka connection open karna
db = SessionLocal()

print("Searching for user...")
# Aapke email se user ko database me dhundna
user = db.query(models.User).filter(models.User.email == "abhi8400673@gmail.com").first()

if user:
    # Role ko 'user' se badal kar 'admin' karna
    user.role = "admin"
    db.commit() # Changes ko database me permanently save karna
    print(f"Success! {user.name} is now an ADMIN! 🎉")
else:
    print("Error: User not found. Please check the email.")

# Database connection close karna
db.close()