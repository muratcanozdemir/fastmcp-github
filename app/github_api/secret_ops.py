import nacl.encoding, nacl.public
from base64 import b64encode

def replace_secret(repo, params):
    name = params["name"]
    value = params["value"]

    try:
        public_key = repo.get_actions_secret_public_key()
        sealed_box = nacl.public.SealedBox(nacl.public.PublicKey(
            public_key.key.encode("utf-8"),
            nacl.encoding.Base64Encoder
        ))
        encrypted = sealed_box.encrypt(value.encode("utf-8"))
        encrypted_value = b64encode(encrypted).decode("utf-8")

        repo.create_or_update_secret(name, encrypted_value, key_id=public_key.key_id)
        return {"status": "secret replaced", "secret": name}
    except GithubException as e:
        print(e)

def delete_secret(repo, params):
    name = params["name"]
    repo.delete_secret(name)
    return {"status": "secret deleted", "secret": name}
