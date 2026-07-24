# FastAPI MFA Backend

A production-style FastAPI backend for authentication, MFA, role-based access, profile management, password recovery, and deployment readiness.

## Overview

This project now demonstrates several backend engineering capabilities that are valuable for recruiters and real-world applications:

- JWT access and refresh token flow
- TOTP-based MFA setup and verification
- Encrypted storage of MFA secrets
- Role-based access control with admin protection
- Password reset and email verification workflows
- Account management endpoints for profile updates and password changes
- Rate limiting for authentication attempts
- Structured logging, CORS support, and health checks
- Docker and Alembic-based migration support

## Quick Start

1. Create and activate a Python virtual environment:

```bash
python -m venv venv
venv\Scripts\activate   # Windows
source venv/bin/activate # macOS / Linux
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start the application:

```bash
python .\app\main.py
```

4. Open the homepage:

```text
http://127.0.0.1:6004/
```

5. Open Swagger docs:

```text
http://127.0.0.1:6004/docs
```

## Core Backend Implementations

### 1. Authentication and session handling
- Implementation: [app/auth.py](app/auth.py), [app/routes/auth.py](app/routes/auth.py)
- Endpoints:
  - POST /auth/register
  - POST /auth/token
  - POST /auth/refresh
- Database usage:
  - Reads and writes the User table for identity and auth state
  - Writes refresh tokens into the RefreshToken table

### 2. MFA security layer
- Implementation: [app/routes/mfa.py](app/routes/mfa.py), [app/utils/crypto.py](app/utils/crypto.py)
- Endpoints:
  - POST /mfa/setup
  - POST /mfa/code
  - POST /mfa/verify
- Database usage:
  - Reads and updates the User table for mfa_enabled and mfa_secret

### 3. Password recovery and email verification
- Implementation: [app/routes/auth.py](app/routes/auth.py), [app/utils/email.py](app/utils/email.py)
- Endpoints:
  - POST /auth/forgot-password
  - POST /auth/reset-password
  - POST /auth/verify-email
- Database usage:
  - Reads/writes PasswordResetToken and EmailVerificationToken tables
  - Sends email notifications through the SMTP configuration in [app/core.py](app/core.py)

### 4. Role-based access control
- Implementation: [app/auth.py](app/auth.py), [app/routes/auth.py](app/routes/auth.py)
- Endpoint:
  - GET /auth/admin/users
- Database usage:
  - Reads the User table and checks the role field

### 5. Account management
- Implementation: [app/routes/auth.py](app/routes/auth.py)
- Endpoints:
  - GET /auth/me
  - PATCH /auth/me
  - POST /auth/change-password
  - POST /auth/deactivate
  - POST /auth/delete-account
- Database usage:
  - Reads and updates the User table

### 6. Database migrations
- Implementation: [alembic](alembic), [alembic.ini](alembic.ini)
- Purpose:
  - Provides versioned schema evolution instead of relying only on startup table creation

### 7. Rate limiting and abuse protection
- Implementation: [app/routes/auth.py](app/routes/auth.py)
- Behavior:
  - Limits repeated login attempts by username and client IP
  - Returns 429 when the threshold is exceeded

### 8. Logging, monitoring, and health checks
- Implementation: [app/main.py](app/main.py)
- Endpoints:
  - GET /health
- Behavior:
  - Adds request validation handling, logging, and CORS middleware

### 9. Deployment readiness
- Implementation: [Dockerfile](Dockerfile), [docker-compose.yml](docker-compose.yml)
- Purpose:
  - Supports containerized deployment and environment-driven configuration

## Recommended Workflow

1. Register with /auth/register
2. Log in with /auth/token to receive access and refresh tokens
3. Use /mfa/setup to generate an authenticator secret and QR code
4. Verify the MFA code with /mfa/verify
5. Use /auth/refresh to rotate your refresh token
6. Recover access with /auth/forgot-password when needed

## License

This project is licensed under the MIT License — see the LICENSE file for details.

## Notes

- The homepage at / serves a documentation-style landing page for the project.
- The app uses SQLite by default, but the settings support PostgreSQL via environment variables.
- For production, update [app/core.py](app/core.py) with a strong SECRET_KEY, secure database settings, HTTPS, CORS, and proper secret management.
