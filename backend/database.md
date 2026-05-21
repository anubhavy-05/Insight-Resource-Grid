# database.py — line-by-line explanation

Below are short, clear explanations for each line in `backend/database.py` so you can understand what each part does.

```python
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
```

1. `from sqlalchemy import create_engine`
   - Imports the `create_engine` function from SQLAlchemy. This function creates an "Engine" object which manages the connection pool and DB dialect.

2. `from sqlalchemy.orm import sessionmaker, declarative_base`
   - Imports two ORM helpers:
     - `sessionmaker`: a factory to produce `Session` objects used to talk to the DB.
     - `declarative_base`: a factory that returns a base class for declaring ORM models (classes mapped to tables).

3. `# Ye hamare database file ka naam hoga jo apne aap ban jayegi`
   - Comment in Hindi: "This will be our database file name which will be created automatically." It documents the next line.

4. `SQLALCHEMY_DATABASE_URL = "sqlite:///./insight.db"`
   - Defines the connection URL for the database.
   - `sqlite:///./insight.db` means use SQLite and store the database file `insight.db` in the current project directory (relative path).
   - For other DBs (Postgres, MySQL) this string would use a different dialect and credentials.

5. `# Engine database se connect karta hai`
   - Comment: "Engine connects to the database." It documents the `engine` creation below.

6. `engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})`
   - Creates the SQLAlchemy `Engine` using the URL above.
   - The `Engine` manages connections and SQL generation.
   - `connect_args={"check_same_thread": False}` is an SQLite-specific option that allows connections to be shared across threads. It's commonly used for web apps running with async frameworks or when multiple threads access the DB. Use with care — for production replace SQLite with a server DB.

7. `# Session database me data dalne aur nikalne ke kaam aata hai`
   - Comment: "Session is used to insert and retrieve data from the database." It documents the `SessionLocal` below.

8. `SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)`
   - Creates a configured `Session` factory named `SessionLocal`.
   - `autocommit=False`: sessions won't auto-commit after each statement — you control when to commit (recommended).
   - `autoflush=False`: disables automatic flushing of pending changes before queries; you can enable it if you want queries to see uncommitted changes in the same session.
   - `bind=engine`: sessions produced by this factory will use the `engine` we created.
   - Typical usage: `db = SessionLocal()` then `db.add(...)`, `db.commit()`, `db.close()` (or use context managers / dependency injection in frameworks like FastAPI).

9. `# Base class jisse hamari saari tables inherit hongi`
   - Comment: "Base class which all our tables will inherit from." It documents `Base` below.

10. `Base = declarative_base()`
    - Creates a base class for ORM model definitions. When you declare a model class, you inherit from `Base`:
      ```py
      class User(Base):
          __tablename__ = "users"
          id = Column(Integer, primary_key=True)
      ```
    - `Base.metadata` holds table metadata and can be used to create tables on the DB with `Base.metadata.create_all(bind=engine)`.

Quick usage notes:
- Use `SessionLocal()` to get a DB session and always close it (or use `with SessionLocal() as db:` when supported).
- For web apps, inject a session per request and `commit()` only when the request succeeds.
- SQLite is fine for development; for production choose a server DB and update `SQLALCHEMY_DATABASE_URL` accordingly.
