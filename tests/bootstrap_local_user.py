# scripts/bootstrap_local_user.py
from jose import jwt
from datetime import datetime, timedelta

JWT_SECRET = "INSECURE-DEFAULT-REPLACE"
JWT_ALGORITHM = "HS256"

fake_user = {
    "sub": "fake-local-user",
    "email": "localuser@example.com",
    "name": "Local Test User",
    "exp": datetime.utcnow() + timedelta(hours=1)
}

token = jwt.encode(fake_user, JWT_SECRET, algorithm=JWT_ALGORITHM)
print(f"Paste into your session cookie: {token}")
