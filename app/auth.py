import os
from datetime import datetime, timedelta

from fastapi import Request, Response, Depends, HTTPException
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from jose import jwt, JWTError

# --- Config ---

oauth = OAuth()
oauth.register(
    name='azure',
    client_id=os.environ["AZURE_AD_CLIENT_ID"],
    client_secret=os.environ["AZURE_AD_CLIENT_SECRET"],
    server_metadata_url=f'https://login.microsoftonline.com/{os.environ["AZURE_AD_TENANT_ID"]}/v2.0/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ALGORITHM = "HS256"
SESSION_COOKIE = "session"

# --- JWT Session ---

def create_jwt_token(userinfo: dict) -> str:
    claims = {
        "sub": userinfo["sub"],
        "email": userinfo.get("email", userinfo.get("preferred_username")),
        "name": userinfo.get("name", ""),
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(claims, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_jwt_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

async def get_current_user(request: Request):
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise HTTPException(status_code=401, detail="Missing session token")
    try:
        return decode_jwt_token(token)
    except JWTError:
        raise HTTPException(status_code=403, detail="Invalid or expired token")

# --- Routes ---

async def login(request: Request):
    redirect_uri = request.url_for("auth_callback")
    return await oauth.azure.authorize_redirect(request, redirect_uri)

async def auth_callback(request: Request):
    token = await oauth.azure.authorize_access_token(request)
    userinfo = await oauth.azure.parse_id_token(request, token)
    jwt_token = create_jwt_token(userinfo)
    response = RedirectResponse(url="/")
    response.set_cookie(
        key=SESSION_COOKIE,
        value=jwt_token,
        httponly=True,
        secure=True,
        max_age=3600
    )
    return response
