import jwt
import sys
import os

# Usage: python decode_jwt_token.py <token>
# Optionally set your SECRET_KEY in .env or as an argument

def main():
    if len(sys.argv) < 2:
        print("Usage: python decode_jwt_token.py <jwt_token> [secret_key]")
        return
    token = sys.argv[1]
    secret = sys.argv[2] if len(sys.argv) > 2 else os.getenv("SECRET_KEY")
    if not secret:
        print("Warning: No SECRET_KEY provided, will decode without verification.")
    try:
        if secret:
            payload = jwt.decode(token, secret, algorithms=["HS256"])
        else:
            payload = jwt.decode(token, options={"verify_signature": False})
        print("Decoded JWT payload:")
        for k, v in payload.items():
            print(f"  {k}: {v}")
    except Exception as e:
        print(f"Error decoding token: {e}")

if __name__ == "__main__":
    main()
