# 01 — Target Application

## Selected Application

**Repository:** `gothinkster/flask-realworld-example-app`  
**Fork URL:** (to be created under your GitHub namespace)  
**Commit SHA (pinned):** `4b95fb2227dfeb5dd1a45d89b2bf48630b93fd28`  
**License:** MIT  
**Language:** Python 3 (Flask)  
**Lines of Code:** ~3,000 (Python + templates)

## What It Does

"Conduit" is a Medium.com clone — a social blogging platform where users can:
- Register and log in (JWT-based authentication via Flask-JWT-Extended)
- Create, read, update, and delete articles
- Comment on articles
- Follow/unfollow other users
- Favorite articles
- View profiles and article feeds

It exposes a full REST API (JSON) with endpoints for all of the above. The backend uses Flask, SQLAlchemy ORM (PostgreSQL), Marshmallow for serialization, and Flask-Bcrypt for password hashing.

## Why This App Was Chosen

| Criterion | Status | Note |
|---|---|---|
| Active repo (commits in last 12 months) | ⚠️ See ADR | Upstream last merge: 2019-09-01. However, the RealWorld project is an actively maintained specification; this Flask implementation is stable and feature-complete. |
| Permissive license | ✅ MIT | |
| Has unit tests | ✅ pytest, 30+ tests | Tests cover auth, articles, profiles, comments |
| Has login form | ✅ JWT-based | Register + login endpoints |
| Has database | ✅ PostgreSQL | Via SQLAlchemy ORM |
| Has REST API | ✅ Full JSON API | CRUD for articles, comments, profiles, auth |
| < 50k LOC | ✅ ~3,000 LOC | |
| Python (Flask) | ✅ | Preferred language per spec |
| Real app (not DVWA) | ✅ | Production-quality reference implementation |

## Application Architecture

```
conduit/
├── app.py              # Flask app factory
├── settings.py         # Configuration (env-based)
├── database.py         # SQLAlchemy setup
├── extensions.py       # Flask extensions (bcrypt, jwt, cors, migrate)
├── commands.py         # CLI commands (db init, etc.)
├── compat.py           # Python 2/3 compatibility
├── exceptions.py       # Custom error handlers
├── utils.py            # Helper utilities
├── user/
│   ├── __init__.py
│   ├── models.py       # User model (email, password hash, bio, image)
│   ├── serializers.py  # Marshmallow schemas
│   └── views.py        # Auth endpoints (register, login, profile)
├── articles/
│   ├── __init__.py
│   ├── models.py       # Article, Comment, Tag models
│   ├── serializers.py
│   └── views.py        # Article/comment CRUD, feed, favorites
└── profile/
    ├── __init__.py
    ├── models.py
    ├── serializers.py
    └── views.py        # Profile follow/unfollow
tests/
├── conftest.py         # Fixtures
├── test_authentication.py
├── test_articles.py
├── test_comments.py
├── test_profiles.py
└── test_tags.py
```

## Security Relevance

This app was chosen specifically because it contains REAL patterns worth scanning:

1. **JWT authentication** — tokens, expiry, refresh logic → testable for session hijacking, replay attacks
2. **SQLAlchemy ORM** — parameterized queries by default, but worth scanning for raw SQL in edge cases
3. **Password hashing** — uses Flask-Bcrypt (bcrypt) → verify hash strength
4. **User input** — article body, comments, bio → testable for XSS, injection
5. **REST API** — auth-required endpoints → testable for privilege escalation, API abuse
6. **CORS configuration** — Flask-Cors → testable for misconfiguration
7. **Error handling** — custom exception handlers → testable for verbose stack traces

## Setup (from the original README)

```bash
# The original app uses pipenv; we'll adapt to requirements.txt
export FLASK_APP=autoapp.py
export FLASK_ENV=development
export DATABASE_URL=postgresql://user:pass@localhost:5432/conduit
export SECRET_KEY=super-secret

pip install -r requirements.txt
flask db upgrade
flask run
```
