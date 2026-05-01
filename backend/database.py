from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Ye hamare database file ka naam hoga jo apne aap ban jayegi
SQLALCHEMY_DATABASE_URL = "sqlite:///./insight.db"

# Engine database se connect karta hai
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Session database me data dalne aur nikalne ke kaam aata hai
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class jisse hamari saari tables inherit hongi
Base = declarative_base()