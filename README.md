# MCP GitHub Control Server

This is a lightweight FastAPI-based server using [FastMCP](https://github.com/mcp-org/fastmcp) to handle GitHub actions on behalf of users authenticated through Azure AD. It runs locally in GitHub Codespaces (or any devcontainer) and interfaces with your GitHub App installation(s) across organizations.

## Features

* Azure AD OAuth2 login flow with secure session cookie
* GitHub App Installation token per-org (via PyGitHub)
* GitHub API action dispatching (repo, team, secret operations)
* Friendly policy engine that modifies user intent (e.g., enforce private repos)
* Audit logging with SQLite
* MCP-compatible endpoints (`/act`, `/me`, `/audit`)
* OpenAPI schema and Swagger UI
* Ready to be used in GitHub Codespaces + VSCode

## Endpoints

| Path             | Method | Description                                             |
| ---------------- | ------ | ------------------------------------------------------- |
| `/`              | GET    | Landing page and API links                              |
| `/login`         | GET    | Start Azure AD login flow                               |
| `/auth/callback` | GET    | OAuth2 callback handler                                 |
| `/me`            | GET    | View identity, orgs, teams, repo access, token metadata |
| `/act`           | POST   | Perform GitHub action on behalf of the user             |
| `/audit`         | GET    | Query audit logs (org admin only)                       |
| `/docs`          | GET    | Swagger UI                                              |
| `/openapi.json`  | GET    | Raw OpenAPI spec                                        |

## GitHub Actions Supported

* `create_repo`
* `delete_repo`
* `replace_secret`
* `delete_secret`
* `add_user_to_team`
* `remove_user_from_team`
* ... extensible via `dispatcher.py`

## Authentication

All requests rely on the browser-based Azure AD OAuth login. After login:

* A secure HTTP-only cookie (`session`) is stored in the browser
* FastAPI dependencies (`get_current_user`) use this to extract the user session
* No manual JWT needed

> Only for testing REST clients (e.g., `.http` files in VSCode), you may manually copy your `session` cookie from DevTools after logging in at `/login`.

## VSCode Integration

### MCP Usage in Codespaces

This server is meant to run inside your `org-management` Codespace and serve as a local MCP instance. You do **not** need to deploy it to the public internet.

1. Open Codespace for your repo
2. The server runs at `localhost:8000`
3. Visit `https://<your-codespace-id>.github.dev:8000/login` to authenticate
4. MCP-compatible tools (like VSCode Copilot agents or CLI) can send requests to `/act` or `/me`

### REST Client Example (`.vscode/rest.http`)

```http
### View identity
GET http://localhost:8000/me
Cookie: session={{your_session_cookie}}

### Run an action (e.g. create repo)
POST http://localhost:8000/act
Content-Type: application/json
Cookie: session={{your_session_cookie}}

{
  "org": "my-org",
  "repo": "",
  "action": "create_repo",
  "parameters": {
    "name": "example-repo",
    "description": "Test repo"
  }
}
```

> Tip: Store cookies via `rest-client.environmentVariables` in `.vscode/settings.json`

### VSCode Task to Open Login Page

Add to `.vscode/tasks.json`:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Login to MCP",
      "type": "shell",
      "command": "xdg-open http://localhost:8000/login || open http://localhost:8000/login",
      "problemMatcher": []
    }
  ]
}
```

---

## Project Structure

```
app/
├── main.py            # FastAPI entrypoint
├── auth.py            # Azure AD + JWT session
├── audit.py           # SQLite + SQLAlchemy async audit log
├── models.py          # Pydantic schemas
├── github_api/
│   ├── dispatcher.py  # GitHub action router
│   ├── authz.py       # Token setup, team membership, admin check
│   ├── identity.py    # /me report builder
│   ├── policy.py      # Friendly enforcement
│   ├── repo_ops.py    # Repo operations
│   ├── secret_ops.py  # Secret ops
│   └── team_ops.py    # Team ops
└── static/
    └── .well-known/
        └── ai-plugin.json
```

## Devcontainer

This is pre-configured to work out-of-the-box with GitHub Codespaces:

* Installs Python tools, Poetry, REST Client, Pylance
* Uses Codespace secrets (no `.env` files)
* Exposes port 8000 for local access

---

## Testing

Use `pytest` to run tests under `tests/`:
```
uv pip install -r requirements.txt
uv pip install .[test]

```

* Policy enforcement tests
* Input validation fuzzing
* Audit API checks
* Identity endpoint behavior

---

## GitHub App Bootstrap

Use `scripts/bootstrap_github_app.py` to:

* Print install URLs
* Decode your private key
* Check installation visibility

This must be followed by manually clicking the “Create App” button on GitHub.

---

## No Deployment Required

This MCP server is meant to run **only inside** the Codespace of your `org-management` repo. It is not intended for production hosting or external service exposure.

Use it as your local authority for GitHub App-powered automation and per-org governance tasks.

## Installation and local dev (if you must)
```
uv pip install hatchling
hatchling build
```



## License

Hobby project as it stands. If it picks up steam internally, might need to move to private.

## Needs envs
AZURE_AD_CLIENT_ID
AZURE_AD_TENANT_ID
AZURE_AD_CLIENT_SECRET
GITHUB_APP_ID
GITHUB_PRIVATE_KEY_BASE64 (we'll decode this to use with PyGitHub)
GITHUB_WEBHOOK_SECRET (optional for webhook verification)
GITHUB_ORGS to cover
AUDIT_DB_URL (e.g., sqlite:///audit.db or postgresql+asyncpg://...)