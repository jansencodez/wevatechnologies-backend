import secrets

# Generate a secure random secret key of 64 bytes (or adjust length as needed)
secret_key = secrets.token_urlsafe(64)

print(f"Your generated JWT_SECRET_KEY: {secret_key}")
