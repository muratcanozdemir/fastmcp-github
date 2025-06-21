from fastapi import FastAPI, Request, Depends, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastmcp import MCPHandler, register_action

from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Counter, Histogram
from slowapi import Limiter, _rate_limiter_exempt
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.decorator import limiter
from fastapi.responses import PlainTextResponse

from typing import Optional, List
import os

from .auth import login, auth_callback, get_current_user
from .models import ActionRequest
from .github_api.identity import get_identity_report
from .github_api.dispatcher import perform_github_action
from .github_api.authz import get_app_client, is_org_admin
from .audit import init_db, log_action, query_audit_logs

app = FastAPI(
    title="MCP GitHub Control Server",
    description="Performs GitHub actions on behalf of authenticated users using GitHub App installations",
    version="0.1.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Prometheus metrics
REQUEST_COUNT = Counter("mcp_requests_total", "Total MCP requests", ["method", "endpoint"])
REQUEST_LATENCY = Histogram("mcp_request_latency_seconds", "Request latency", ["endpoint"])

limiter = Limiter(key_func=get_rate_limit_key)

def get_rate_limit_key(request: Request) -> str:
    token = request.cookies.get("session")
    if not token:
        return get_remote_address(request)
    try:
        user = decode_jwt_token(token)
        return user.get("email", get_remote_address(request))
    except JWTError:
        return get_remote_address(request)


app.mount("/.well-known", StaticFiles(directory="app/static/.well-known"), name="well-known")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, lambda request, exc: PlainTextResponse("Too Many Requests", status_code=429))


@app.middleware("http")
async def rate_limiter(request: Request, call_next):
    response = await limiter.middleware(request, call_next)
    return response

@app.get("/metrics", include_in_schema=False)
def metrics():
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/healthz", tags=["meta"], summary="Basic health check", include_in_schema=True)
def healthz():
    return {"status": "ok"}

@app.middleware("http")
async def metrics_and_ratelimit(request: Request, call_next):
    endpoint = request.url.path
    method = request.method

    start_time = time.time()
    try:
        response = await limiter.middleware(request, call_next)
    finally:
        duration = time.time() - start_time
        REQUEST_LATENCY.labels(endpoint=endpoint).observe(duration)
        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()

    return response


@app.on_event("startup")
async def startup_event():
    await init_db()

# Azure AD OAuth entrypoints
app.add_route("/login", login, methods=["GET"])
app.add_route("/auth/callback", auth_callback, methods=["GET"])

# Open CORS for Codespaces/VSC integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

mcp = MCPHandler(app)

@app.get("/", tags=["meta"], summary="Landing page for the MCP Server")
async def root():
    return {
        "message": "Welcome to the MCP GitHub Server",
        "docs": "/docs",
        "openapi": "/openapi.json",
        "actions": ["/act", "/audit", "/me"],
        "auth": ["/login", "/auth/callback"]
    }

@app.post("/act")
@register_action(
    name="github/act",
    tags=["github"],
    summary="Perform GitHub action on behalf of user",
    permissions=["write"]
)
@limiter("5/minute")
async def act_on_github(
    request: Request,
    action: ActionRequest,
    user=Depends(get_current_user)
):
    """
    Dispatch a GitHub action (e.g., create repo, manage secrets) using GitHub App installation token.
    """
    try:
        result = await perform_github_action(action=action, user=user)
        await log_action(user=user, action=action, result="success")
        return {"status": "ok", "details": result}
    except Exception as e:
        await log_action(user=user, action=action, result=f"error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"GitHub action failed: {e}")

@app.get("/audit", response_model=List[dict], tags=["admin"], summary="Query audit logs (org admins only)")
async def audit_logs(
    user=Depends(get_current_user),
    email: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    org: Optional[str] = Query(None),
    repo: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    if not org:
        raise HTTPException(status_code=400, detail="`org` parameter is required")

    gh = get_app_client(org)
    username = user["email"].split("@")[0]
