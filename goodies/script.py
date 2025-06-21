#!/usr/bin/env python3
import json
import urllib.parse
import sys

MANIFEST_FILE = "github-app-manifest.json"
GITHUB_CREATE_URL = "https://github.com/settings/apps/new"

def load_manifest():
    try:
        with open(MANIFEST_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Failed to load {MANIFEST_FILE}: {e}")
        sys.exit(1)

def encode_manifest_url(manifest: dict) -> str:
    manifest_json = json.dumps(manifest, separators=(",", ":"))
    encoded = urllib.parse.quote_plus(manifest_json)
    return f"{GITHUB_CREATE_URL}?manifest={encoded}"

def main():
    print("📦 Preparing GitHub App manifest for browser flow...")
    manifest = load_manifest()
    url = encode_manifest_url(manifest)

    print("\n✅ GitHub App manifest prepared.")
    print("👉 Visit this URL to create your GitHub App:\n")
    print(f"  {url}\n")
    print("⚠️ After clicking 'Create GitHub App', GitHub will show:")
    print("  - App ID")
    print("  - Client ID / Client Secret")
    print("  - Webhook secret")
    print("  - Private key download")
    print("📥 Inject these into your Codespace as secrets.")

if __name__ == "__main__":
    main()
