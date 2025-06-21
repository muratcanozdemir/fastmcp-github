from github import Github, GithubIntegration, GithubException
import base64
import os

GITHUB_APP_ID = int(os.environ["GITHUB_APP_ID"])
GITHUB_PRIVATE_KEY = base64.b64decode(os.environ["GITHUB_PRIVATE_KEY_BASE64"]).decode("utf-8")

integration = GithubIntegration(GITHUB_APP_ID, GITHUB_PRIVATE_KEY)

def get_app_client(org: str, repo: str = None) -> Github:
    try:
        installation = integration.get_installation(org, repo) if repo else integration.get_organization_installation(org)
        access_token = integration.get_access_token(installation.id).token
        return Github(access_token)
    except GithubException as e:
        raise raise GithubException(f"GitHub App installation not found for org={org}, repo={repo}: {e}")

def check_team_membership(client: Github, org: str, team_slug: str, username: str) -> bool:
    try:
        team = client.get_organization(org).get_team_by_slug(team_slug)
        return team.has_in_members(username)
    except GithubException:
        return False

def is_org_admin(client: Github, org: str, username: str, allowed_teams=None) -> bool:
    allowed_teams = allowed_teams or ["owners", "mcp-auditors"]
    gh_org = client.get_organization(org)

    for team_slug in allowed_teams:
        try:
            team = gh_org.get_team_by_slug(team_slug)
            if team.has_in_members(username):
                return True
        except GithubException:
            continue
    return False

__all__ = ["get_app_client", "check_team_membership", "is_org_admin", "integration"]
