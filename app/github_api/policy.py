from ..models import ActionRequest

DEFAULT_TEAM = "infrastructure-admins"

def enforce_policy(action: ActionRequest, user: dict) -> ActionRequest:
    """
    Friendly policy layer to auto-correct or improve user requests.
    """
    modified = action.dict()

    action_type = modified["action"]
    params = modified["parameters"] or {}
    email_prefix = user["email"].split("@")[0]

    if action_type == "create_repo":
        if not params.get("private"):
            params["private"] = True  # enforce private repos by default
        if not params["name"].startswith("dev-"):
            params["name"] = f"dev-{params['name']}"
        if not params.get("description"):
            params["description"] = f"Repository created by {email_prefix} via MCP"

    if action_type == "replace_secret":
        if "name" in params and not params["name"].startswith("MCP_"):
            params["name"] = f"MCP_{params['name']}"

    if "team" not in params:
        params["team"] = "infrastructure-admins"

    modified["parameters"] = params
    return ActionRequest(**modified)
