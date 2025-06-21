import os
from cachetools import TTLCache, cached
from .authz import get_app_client, is_org_admin
from github import GithubException
from datetime import datetime

from .authz import integration

# Caches
_membership_cache = TTLCache(maxsize=256, ttl=300)
_repos_cache      = TTLCache(maxsize=256, ttl=300)
_token_cache      = TTLCache(maxsize=256, ttl=300)

@cached(_membership_cache)
def get_user_membership(username: str, org: str) -> dict:
    try:
        gh = get_app_client(org)
        org_obj = gh.get_organization(org)
        teams = [t.slug for t in org_obj.get_teams() if t.has_in_members(username)]
        return {"teams": teams}
    except Exception as e:
        return {"error": str(e)}

@cached(_repos_cache)
def get_installation_repos(org: str) -> list[str]:
    try:
        gh = get_app_client(org)
        return [r.full_name for r in gh.get_organization(org).get_repos()]
    except Exception:
        return []

@cached(_token_cache)
def get_installation_metadata(org: str) -> dict:
    try:
        inst = integration.get_organization_installation(org)
        token = integration.get_access_token(inst.id)
        return {
            "expires_at": token.expires_at.isoformat(),
            "permissions": token.permissions,
        }
    except GithubException as e:
        return {"error": str(e)}

def get_identity_report(user: dict) -> dict:
    username = user.get("email", "").split("@")[0]
    report = {
        "email": user.get("email"),
        "name": user.get("name"),
        "username": username,
        "github": {},
        "flags": {}
    }

    orgs = [o.strip() for o in os.getenv("GITHUB_ORGS", "").split(",") if o.strip()]
    for org in orgs:
        teams = get_user_membership(username, org).get("teams", [])
        repos = get_installation_repos(org)
        token_meta = get_installation_metadata(org)
        admin = is_org_admin(get_app_client(org), org, username)

        report["github"][org] = {
            "teams": teams,
            "accessible_repos": repos,
            "token": token_meta
        }
        report["flags"][org] = {"is_admin": admin}

    return report
