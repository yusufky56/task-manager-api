# Task Manager API

![CI](https://github.com/yusufky56/task-manager-api/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue)

A REST API for managing personal tasks. Users sign up, log in with a JWT token and manage their own tasks with filtering, search, sorting and pagination.

Built with **FastAPI**, **SQLAlchemy 2.0** and **Pydantic v2**.

## Features

- Registration and login with JWT access tokens (OAuth2 password flow)
- Passwords hashed with PBKDF2-SHA256 and a random salt
- Full CRUD for tasks, scoped to the logged-in user
- Filter by status and priority, full-text search in title and description
- Sorting and limit/offset pagination
- Statistics endpoint: counts per status and number of overdue tasks
- Interactive API docs at `/docs` (Swagger UI)
- 17 tests with an isolated in-memory database, run on CI for Python 3.11–3.13

## Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/auth/register` | Create an account |
| `POST` | `/auth/login` | Get an access token |
| `GET` | `/auth/me` | Current user |
| `GET` | `/tasks` | List tasks (`status`, `priority`, `q`, `sort`, `order`, `limit`, `offset`) |
| `POST` | `/tasks` | Create a task |
| `GET` | `/tasks/stats` | Task statistics |
| `GET` | `/tasks/{id}` | Get a task |
| `PATCH` | `/tasks/{id}` | Update a task |
| `DELETE` | `/tasks/{id}` | Delete a task |
| `GET` | `/health` | Health check |

## Getting started

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env             # set SECRET_KEY
uvicorn app.main:app --reload
```

Open http://localhost:8000/docs to try the API.

### With Docker

```bash
docker build -t task-manager-api .
docker run -p 8000:8000 -e SECRET_KEY=your-secret task-manager-api
```

## Example

```bash
curl -X POST localhost:8000/auth/register -H "Content-Type: application/json" \
     -d '{"email": "me@example.com", "password": "secret123"}'

TOKEN=$(curl -s -X POST localhost:8000/auth/login \
     -d "username=me@example.com&password=secret123" | jq -r .access_token)

curl -X POST localhost:8000/tasks -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"title": "Finish report", "priority": "high", "due_date": "2026-12-01"}'

curl "localhost:8000/tasks?priority=high&sort=due_date&order=asc" -H "Authorization: Bearer $TOKEN"
```

## Project structure

```
app/
├── main.py          # App setup and routers
├── config.py        # Settings from environment variables
├── database.py      # Engine, session, Base
├── models.py        # SQLAlchemy models: User, Task
├── schemas.py       # Pydantic request/response models
├── security.py      # Password hashing and JWT
├── deps.py          # Shared dependencies (DB session, current user)
└── routers/
    ├── auth.py
    └── tasks.py
tests/               # pytest suite
```

## Running tests

```bash
pytest
```

## License

[MIT](LICENSE)
