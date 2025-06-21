```curl -X POST https://api.github.com/app-manifests/convert \
  -H "Accept: application/vnd.github+json" \
  -H "Content-Type: application/json" \
  -d @github-app-manifest.json```

This will convert your app manifest into an app.
1) A pop up will appear, where you'll have to click on Create GitHub App.
2) Callback URL will be this server, so you will catch the id, slug, pem, client_id and client_secret naturally.
3) Save them as Codespace secrets.