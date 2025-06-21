def add_user_to_team(org, params):
    team_slug = params["team"]
    username = params["username"]
    team = org.get_team_by_slug(team_slug)
    team.add_membership(username)
    return {"status": "user added", "team": team_slug, "user": username}

def remove_user_from_team(org, params):
    team_slug = params["team"]
    username = params["username"]
    team = org.get_team_by_slug(team_slug)
    team.remove_membership(username)
    return {"status": "user removed", "team": team_slug, "user": username}
