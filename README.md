# Insight Resource Grid

This project has two main parts:

- `backend` for the FastAPI server and database
- `frontend` for the simple HTML page that shows approved resources

If you are new, start with these files:

- [backend/README.md](backend/README.md)
- [frontend/README.md](frontend/README.md)

## Project Files

- [backend/database.py](backend/database.py) - Database connection setup
- [backend/main.py](backend/main.py) - Main API file
- [backend/make_admin.py](backend/make_admin.py) - Small script to make a user admin
- [backend/models.py](backend/models.py) - Database table models
- [backend/schemas.py](backend/schemas.py) - Data shapes used by the API
- [frontend/index.html](frontend/index.html) - Simple frontend page

## How It Works

1. User signs up or logs in from the backend API.
2. User submits a resource.
3. Admin approves the resource.
4. Frontend shows only approved resources.

## Simple Start

- Read the backend README first if you want to understand the API.
- Read the frontend README if you want to understand the page.
- Open `backend/main.py` if you want to see the full flow.