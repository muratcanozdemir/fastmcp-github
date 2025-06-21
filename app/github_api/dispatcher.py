from .repo_ops import create_repo, delete_repo, create_issue
from .secret_ops import replace_secret, delete_secret
from .team_ops import add_user_to_team, remove_user_from_team
from .authz import get_app_client, check_team_membership
from .policy import enforce_policy
from ..models import ActionRequest

class UnauthorizedError(Exception): pass

async def perform_github_action(action: ActionRequest, user: dict):
    org = action.org
    repo = action.repo
    action_type = action.action
    params = action.parameters or {}

    # Normalize & enhance request via policy rules
    cleaned_action = enforce_policy(action, user)

    gh = get_app_client(org, repo if repo else None)

    if not check_team_membership(gh, org, cleaned_action.parameters.get("team", "infrastructure-admins"), user["email"].split("@")[0]):
        raise UnauthorizedError("User not in required team")

    dispatch_table = {
        "create_repo": create_repo,
        "delete_repo": delete_repo,
        "replace_secret": replace_secret,
        "delete_secret": delete_secret,
        "add_user_to_team": add_user_to_team,
        "remove_user_from_team": remove_user_from_team,
    }


    if action_type not in dispatch_table:
        raise Exception(f"Unknown action: {action_type}")

    target = gh.get_repo(f"{org}/{repo}") if repo else gh.get_organization(org)
    return dispatch_table[action_type](target, cleaned_action.parameters)
