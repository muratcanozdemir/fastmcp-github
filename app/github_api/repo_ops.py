def create_repo(org, params):
    name = params["name"]
    private = params.get("private", True)
    description = params.get("description", "")
    repo = org.create_repo(name=name, private=private, description=description)
    return {"status": "created", "url": repo.html_url}

def delete_repo(org, params):
    name = params["name"]
    repo = org.get_repo(name)
    repo.delete()
    return {"status": "deleted", "repo": name}

def create_issue(repo, params):
    issue = repo.create_issue(
        title=params["title"],
        body=params.get("body", "")
    )
    return {
        "status": "issue created",
        "url": issue.html_url,
        "number": issue.number
    }