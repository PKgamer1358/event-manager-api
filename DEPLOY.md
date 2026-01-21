# Deployment Guide for Render

This API is configured for deployment on [Render](https://render.com/).

## Prerequisites

1. **GitHub Repository**: Ensure your code is pushed to a GitHub repository.
2. **Render Account**: Create an account on Render.
3. **PostgreSQL Database**: You will need a PostgreSQL database. You can create one on Render or use an external provider.

## Deployment Steps

### Method 1: Blueprint (Recommended)

1. Go to your Render Dashboard.
2. Click **New +** and select **Blueprint**.
3. Connect your GitHub repository.
4. Render will detect the `render.yaml` file.
5. You will be prompted to provide values for the following Environment Variables:
   - `DATABASE_URL`: Your PostgreSQL connection string (e.g., `postgres://user:password@host/dbname`).
   - `FIREBASE_CREDENTIALS`: The content of your `app/core/firebase-service-account.json` file.
     > **Important**: Copy the entire content of the JSON file and paste it as the value. ensure it is valid JSON.
   - `SECRET_KEY`: Render may generate this for you, or you can provide a strong random string.

### Method 2: Manual Web Service

1. Create a new **Web Service** on Render.
2. Connect your GitHub repository.
3. Use the following settings:
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add the following **Environment Variables**:
   - `DATABASE_URL`: Connection string to your database.
   - `SECRET_KEY`: A secure random string.
   - `FIREBASE_CREDENTIALS`: Content of your `app/core/firebase-service-account.json`.
   - `PYTHON_VERSION`: `3.10.13`

## Firebase Credentials

The application is updated to read Firebase credentials from the `FIREBASE_CREDENTIALS` environment variable.
To set this up:
1. Open your local `app/core/firebase-service-account.json`.
2. Copy the entire content.
3. Paste it into the `FIREBASE_CREDENTIALS` value field in Render.

## Database Migrations

The start command is configured to run `alembic upgrade head` automatically on every deployment. This ensures your database schema is always up to date.
