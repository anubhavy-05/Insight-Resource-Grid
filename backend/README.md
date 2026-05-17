# Backend README

This folder has the Python API and database code.

## Files In This Folder

- [database.py](database.py) - Connects the app to SQLite and creates the session.
- [main.py](main.py) - Main FastAPI app. It handles signup, login, resource upload, approval, delete, and profile routes.
- [make_admin.py](make_admin.py) - Helper script to turn one user into an admin.
- [models.py](models.py) - SQLAlchemy models for `User` and `Resource`.
- [schemas.py](schemas.py) - Pydantic schemas for request and response data.
- [README.md](README.md) - This help file.

## Main Idea

- `User` stores name, email, password hash, role, and active status.
- `Resource` stores title, description, link, status, and the user who uploaded it.
- `main.py` uses these tables to control the app.

## Easy Flow

1. A user signs up.
2. The user logs in and gets a token.
3. The user uploads a resource.
4. An admin approves or deletes the resource.
5. The frontend shows only approved resources.

## Important Notes

- SQLite database file: `insight.db`
- Login uses the email as the username field in Swagger UI.
- Approved resources are the only ones shown by the public GET route.
