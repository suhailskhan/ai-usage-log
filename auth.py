import os
import time
import jwt

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your-very-secret-key")  # Fallback for local development
JWT_ALGORITHM = "HS256"

# Extract domain from STREAMLIT_APP_URL or use localhost
app_url = os.getenv("STREAMLIT_APP_URL", "localhost")
if app_url.startswith("https://"):
    JWT_AUDIENCE = app_url[8:]  # Remove "https://"
elif app_url.startswith("http://"):
    JWT_AUDIENCE = app_url[7:]   # Remove "http://"
else:
    JWT_AUDIENCE = app_url

JWT_ISSUER = "AI Usage Log"
JWT_SUBJECT = "Suhail Khan"
JWT_EXP_DELTA_SECONDS = 60 * 60 * 24 * 365  # 1 year

def create_jwt():
    now = int(time.time())
    payload = {
        "iss": JWT_ISSUER,
        "iat": now,
        "exp": now + JWT_EXP_DELTA_SECONDS,
        "aud": JWT_AUDIENCE,
        "sub": JWT_SUBJECT
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token

def validate_jwt(token):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM], audience=JWT_AUDIENCE, issuer=JWT_ISSUER)
        return payload
    except jwt.PyJWTError as e:
        return None
