# Frontend README

This folder has the simple web page that shows approved resources from the backend.

## File In This Folder

- [index.html](index.html) - The page that loads resource data and shows it on screen.

## What It Does

- Opens a basic page with a title.
- Calls the backend API at `http://127.0.0.1:8000/resources/`.
- Shows each approved resource in a card.
- Shows the resource title, description, uploader ID, and link.

## Simple Flow

1. Open the HTML file in a browser.
2. The page asks the backend for approved resources.
3. The backend sends JSON data.
4. The page prints the data on screen.

## Easy Note

- If the backend is not running, the page will show an error message.
- If you change the backend URL, update it in `index.html`.