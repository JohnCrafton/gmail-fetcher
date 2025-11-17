# OAuth Setup for SSH/Remote Servers

If you're running Gmail Fetcher on a remote server over SSH, OAuth authentication needs special handling since it requires browser access.

## Recommended: Generate Token Locally

**Easiest and most reliable method:**

### On Your Local Machine

```bash
# 1. Clone repo locally
git clone <repo-url>
cd gmail-fetcher

# 2. Copy credentials
cp ~/Downloads/client_secret_*.json secrets/credentials.json

# 3. Run OAuth setup
./setup-oauth.sh
# Or manually:
# uv venv && uv pip install -r requirements.txt
# source .venv/bin/activate
# python gmail-fetcher.py

# Browser opens automatically, you authorize
# Token saved to: data/token.json
```

### Copy Token to Server

```bash
# Copy to remote server
scp data/token.json user@remote-host:/path/to/gmail-fetcher/data/

# Or if using Docker volume
scp data/token.json user@remote-host:/media/12TB/backup/gmail_data/
```

### Run on Server

```bash
# SSH to server
ssh user@remote-host

# Run Gmail Fetcher (token already exists)
cd /path/to/gmail-fetcher
docker compose up
```

**Done!** No SSH tunneling, no manual code copying, works every time.

---

## Alternative: SSH Port Forwarding

If you can't generate the token locally, use SSH port forwarding to redirect the OAuth callback.

### Setup

```bash
# On your LOCAL machine, connect with port forward
ssh -L 8080:localhost:8080 user@remote-host

# This forwards port 8080 from remote to your local machine
```

### Run OAuth on Remote

```bash
# On the REMOTE server (in SSH session)
cd /path/to/gmail-fetcher
source .venv/bin/activate

# Run WITHOUT --no-auth-browser
python gmail-fetcher.py
```

### What Happens

1. Script starts local HTTP server on port 8080 (remote side)
2. Browser URL is displayed
3. You open it in your LOCAL browser (thanks to port forward)
4. After authorization, Google redirects to `http://localhost:8080/?code=...`
5. Your LOCAL browser connects to REMOTE server's port 8080
6. Script receives the code and completes authentication
7. Token saved on remote server

### If Browser Doesn't Open Automatically

```bash
# The script will show a URL like:
# http://localhost:8080/...

# Manually copy and paste it into your browser
# Everything else works the same
```

---

## Third Option: Manual Code Extraction (Advanced)

If port forwarding doesn't work, you can manually extract the authorization code.

### Run with Manual Flag

```bash
python gmail-fetcher.py --no-auth-browser
```

### Steps

1. Script displays authorization URL
2. Copy URL and open in your LOCAL browser
3. Authorize the application
4. Google redirects to `http://localhost:8080/?code=4/0AbC...&scope=...`
5. Browser shows "Connection refused" or similar (expected!)
6. Copy the ENTIRE URL from your browser's address bar
7. Back in SSH terminal, paste it when prompted
8. Script extracts the code and completes authentication

**Note**: The script will parse the code from the URL automatically.

---

## Troubleshooting

### "Redirect URI mismatch"

Desktop app credentials support `localhost` automatically. Make sure you're using **Desktop app** type, not Web application.

### "Connection refused" in Browser

This is **expected** if not using port forwarding. Just copy the URL from the address bar - the code is in there.

### "Could not locate runnable browser"

You're on a headless server. Use one of these:
- **Recommended**: Generate token locally (Option 1)
- Use SSH port forwarding (Option 2)
- Use `--no-auth-browser` (Option 3)

### Port 8080 Already in Use

The script picks a random port. If you get this error:
```bash
# For port forwarding, use the actual port shown
# Example: if script uses port 54321
ssh -L 54321:localhost:54321 user@remote-host
```

### Token Works Locally but Not on Server

Make sure you copied `token.json` to the correct location:
- Docker: `/media/12TB/backup/gmail_data/token.json` (or wherever data volume is mounted)
- Local: `./data/token.json`

Check permissions:
```bash
chmod 600 data/token.json
chown yourusername:yourgroup data/token.json
```

---

## Security Notes

### SSH Port Forwarding Safety

- ✅ Port is only forwarded locally (not exposed to network)
- ✅ Only you can access `localhost:8080` during OAuth
- ✅ Connection encrypted via SSH
- ✅ OAuth code expires quickly

### Token Security

- Keep `token.json` secure (chmod 600)
- Never commit to git (.gitignore protects you)
- Token grants full Gmail access - protect like a password
- Can revoke anytime at https://myaccount.google.com/permissions

---

## Quick Reference

### Method 1: Local Token (Easiest) ⭐
```bash
# Local: ./setup-oauth.sh
# Copy: scp data/token.json user@host:/path/
# Remote: docker compose up
```

### Method 2: Port Forward
```bash
# Local: ssh -L 8080:localhost:8080 user@host
# Remote: python gmail-fetcher.py
```

### Method 3: Manual Code
```bash
# Remote: python gmail-fetcher.py --no-auth-browser
# Copy URL from browser, paste back
```

**Recommendation**: Use Method 1 (Local Token) - it's the most reliable.
