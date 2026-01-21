# Event Manager API

A FastAPI-based event management system with PostgreSQL database, JWT authentication, and Swagger documentation.

## Features

- 🔐 User authentication with JWT tokens (OAuth2PasswordBearer)
- 👥 User roles (admin/regular users)
- 📅 Event creation and management (admin only)
- ✅ Event registration system with capacity management
- 📊 Swagger/OpenAPI documentation (automatic)
- 🗄️ PostgreSQL database with SQLAlchemy ORM
- 🔄 Database migrations with Alembic
- 🌐 CORS support for frontend integration
- ✨ Pydantic validation for request/response

## Prerequisites

- Python 3.10+
- PostgreSQL database
- [uv](https://github.com/astral-sh/uv) package manager (or pip)

## Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd event-manager-api
```

### 2. Create virtual environment and install dependencies

Using uv (recommended):

```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

Or using pip:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

### 3. Set up PostgreSQL database

Create the database:

```bash
createdb event-manager
```

Or using psql:

```bash
psql postgres -c "CREATE DATABASE \"event-manager\""
```

### 4. Configure environment variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and update the following:

```env
# Database - Update with your PostgreSQL credentials
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/event-manager

# JWT Secret - Generate a secure random key for production
SECRET_KEY=your-secret-key-here-change-in-production

# Optional: Update CORS origins if needed
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080
```

**Note:** If your password contains special characters (like `@`), you must URL-encode them:

- `@` becomes `%40`
- Example: `Welcome@1` becomes `Welcome%401`

### 5. Run database migrations

```bash
alembic upgrade head
```

This will create all the necessary tables (users, colleges, students, events, registrations).

### 6. Start the server

```bash
uvicorn app.main:app --reload
```

Or for production:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 7. Access the API

- **API Base**: http://localhost:8000
- **Swagger UI** (interactive docs): http://localhost:8000/docs
- **ReDoc** (alternative docs): http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## API Endpoints

### Authentication

- `POST /api/auth/signup` - Register a new user
- `POST /api/auth/login` - Login and get JWT access token
- `GET /api/auth/me` - Get current user information

### Events

- `GET /api/events` - List all events (authenticated)
- `GET /api/events/{event_id}` - Get event details
- `POST /api/events` - Create new event (admin only)
- `DELETE /api/events/{event_id}` - Delete event (admin only)

### Registrations

- `POST /api/registrations/events/{event_id}/register` - Register for an event
- `DELETE /api/registrations/events/{event_id}/register` - Unregister from an event
- `GET /api/registrations/events/{event_id}/registrations` - Get event registrations (admin/creator only)
- `GET /api/registrations/my-registrations` - Get current user's registrations

## Quick Start Guide

### 1. Create an admin user

Using Swagger UI (http://localhost:8000/docs):

1. Go to `POST /api/auth/signup`
2. Click "Try it out"
3. Use this JSON:
   ```json
   {
     "email": "admin@example.com",
     "password": "admin123",
     "full_name": "Admin User",
     "is_admin": true
   }
   ```
4. Click "Execute"

### 2. Login and get access token

1. Go to `POST /api/auth/login`
2. Click "Try it out"
3. Enter:
   - Username: `admin@example.com`
   - Password: `admin123`
4. Copy the `access_token` from the response

### 3. Authorize in Swagger

1. Click the "Authorize" button at the top of Swagger UI
2. Enter: `Bearer <your_access_token>`
3. Click "Authorize"

Now you can test all protected endpoints!

## Development

### Running with auto-reload

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Updating your database after pulling changes

If you've pulled the latest changes from git and there are new database migrations:

```bash
# Activate virtual environment
source .venv/bin/activate

# Check current database version
python -m alembic current

# View available migrations
python -m alembic heads

# Apply all pending migrations
python -m alembic upgrade head
```

The `upgrade head` command will:

- Check which migrations have already been applied
- Apply any new migrations in sequence
- Update your database schema to match the latest models

### Creating new migrations

After modifying models:

```bash
python -m alembic revision --autogenerate -m "Description of changes"
python -m alembic upgrade head
```

**Important:** Always review auto-generated migrations before applying them. Alembic may not detect all changes correctly (like column renames or data migrations).

### Project Structure

```
event-manager-api/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app configuration
│   ├── config.py            # Settings and environment variables
│   ├── database.py          # Database connection
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── dependencies.py      # Auth dependencies
│   └── routers/             # API route modules
│       ├── auth.py          # Authentication endpoints
│       ├── users.py         # User management endpoints
│       ├── colleges.py      # College endpoints
│       ├── events.py        # Event endpoints
│       └── registrations.py # Registration endpoints
├── alembic/                 # Database migrations
├── .env                     # Environment variables (not in git)
├── .env.example             # Example environment file
├── pyproject.toml           # Project dependencies
└── README.md
```

## Troubleshooting

### Database connection issues

If you see `password authentication failed`:

1. Verify PostgreSQL is running: `pg_isready`
2. Check your DATABASE_URL in `.env`
3. Ensure special characters in password are URL-encoded

### Bcrypt password errors

The app automatically handles password length limits. If you encounter issues, ensure `passlib[bcrypt]` is installed.

### Port already in use

If port 8000 is busy:

```bash
uvicorn app.main:app --reload --port 8001
```

## Testing

The API includes Swagger UI for interactive testing at http://localhost:8000/docs

## License

MIT
