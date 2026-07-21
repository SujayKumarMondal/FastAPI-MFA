# FastAPI MFA Backend

A polished FastAPI backend for JWT authentication and TOTP-based MFA, with a built-in homepage and interactive docs.

## Overview

This project delivers a secure authentication backend featuring:

- JWT bearer token login
- TOTP MFA setup using Authenticator apps
- Encrypted MFA secret storage
- Built-in homepage documentation at `http://localhost:6004/`
- Swagger UI available at `http://localhost:6004/docs`

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
python .\\app\\main.py
```

4. Open the homepage:

```text
http://127.0.0.1:6004/
```

5. Open Swagger docs:

```text
http://127.0.0.1:6004/docs
```

## Core Endpoints

- `POST /auth/register`
	- Register a new user account.
- `POST /auth/token`
	- Authenticate with username/password and receive a JWT access token.
	- If MFA is enabled, include `mfa_token` in the form data.
- `POST /mfa/setup`
	- Generate or retrieve the TOTP secret for the logged-in user.
	- Returns `secret`, `otpauth_url`, and `qr_code_data_url`.
- `POST /mfa/code`
	- Generate the current 6-digit TOTP code for a user when given:
		- `username`
		- `access_token`
		- `secret`
- `POST /mfa/verify`
	- Verify Authenticator app codes and enable MFA for the user.
	- Requires `username`, `access_token`, and `token`.

## Recommended Workflow

1. Register with `/auth/register`
2. Log in with `/auth/token` to receive a JWT
3. Use `/mfa/setup` to generate an Authenticator secret and QR code
4. Scan the QR code in Google Authenticator or Authy
5. Verify the first code with `/mfa/verify`
6. Log in again with `/auth/token`, including `mfa_token`

## License

This project is licensed under the MIT License — see the `LICENSE` file for details.

## Notes

- The homepage at `/` serves a documentation-style landing page for the project.
- The app uses SQLite by default, but the settings support PostgreSQL via environment variables.
- For production, update `app/core.py` with a strong `SECRET_KEY`, secure database settings, HTTPS, CORS, and proper secret management.
