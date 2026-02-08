import secrets

# Generate a 32-byte (256-bit) secret key
secret_key = secrets.token_hex(32)
print(f"Generated Secret Key: {secret_key}")
<<<<<<< HEAD
print("\nAdd this to your .env file:")
=======
print("\nAdd this to your DB.env file:")
>>>>>>> 2e63df1f0f450d9840f69fb32e58b7c42ce5e21c
print(f"SECRET_KEY={secret_key}")