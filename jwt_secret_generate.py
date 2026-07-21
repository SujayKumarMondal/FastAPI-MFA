import secrets

# Generate a random JWT secret key
JWT_SECRET = secrets.token_hex(32)

print("Generated JWT Secret:", JWT_SECRET)
