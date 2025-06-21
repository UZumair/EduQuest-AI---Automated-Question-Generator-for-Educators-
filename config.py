# File: utils/config.py
import os
import secrets

# Generate a secure key if not exists
SECRET_KEY = os.getenv("EDUQUEST1024029", secrets.token_hex(32))