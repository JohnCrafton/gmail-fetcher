# OAuth Setup Guide

Getting Gmail API access set up properly.

## Quick Setup (Recommended)

```bash
./setup-oauth.sh
```

This automated script will:
1. Check for credentials.json
2. Install uv and dependencies
3. Guide you through OAuth
4. Save token to `data/token.json`
5. Give you next steps

## Manual Setup

### 1. Get Gmail API Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable Gmail API:
   - APIs & Services → Library
   - Search "Gmail API"
   - Click Enable
4. Create OAuth credentials:
   - APIs & Services → Credentials
   - Create Credentials → OAuth client ID
   - Application type: **Desktop app**
   - Name it something like "Gmail Fetcher"
   - Download JSON
5. Save as `secrets/credentials.json`

### 2. Configure OAuth Redirect URIs

In Google Cloud Console:
1. Go to APIs & Services → Credentials
2. Click your OAuth 2.0 Client ID
3. Under "Authorized redirect URIs", add these:
   - `urn:ietf:wg:oauth:2.0:oob` (for manual code flow)
   - `http://localhost` (for local browser flow)
   - `http://127.0.0.1` (for local browser flow)
4. Save

**Note**: The `urn:ietf:wg:oauth:2.0:oob` is required for the `--no-auth-browser` manual flow.

### 3. Run OAuth Flow

**Option A: Using the helper script (easiest)**
```bash
./setup-oauth.sh
```

**Option B: Manually**
```bash
# Install dependencies
uv venv
uv pip install -r requirements.txt
source .venv/bin/activate

# Run OAuth
python gmail-fetcher.py --no-auth-browser
```

### 4. Follow the Prompts

The script will:
1. Display a URL
2. Ask you to paste an authorization code

**In your browser:**
1. Open the URL
2. Sign in to Gmail
3. Click "Continue" or "Allow"
4. Copy the authorization code shown
5. Paste it into the terminal

**Result:** Token saved to `data/token.json`

## For Docker Deployment

After getting `data/token.json` locally:

**Option 1: Copy to Docker volume**
```bash
cp data/token.json /media/12TB/backup/gmail_data/
```

**Option 2: Mount local data directory**

Edit `docker-compose.yml`:
```yaml
volumes:
  # - /media/12TB/backup/gmail_data:/data  # Comment out
  - ./data:/data  # Use local data directory
```

Then:
```bash
docker compose up
```

## SSH/Remote Setup

If you're working over SSH and the OAuth callback isn't working:

### Option 1: SSH Port Forwarding
```bash
# On your local machine
ssh -L 8080:localhost:8080 user@remote-host

# Then on remote machine
python gmail-fetcher.py
# Browser opens on your local machine, callback works
```

### Option 2: Manual Flow (No Browser)
```bash
# On remote machine
python gmail-fetcher.py --no-auth-browser

# Manually copy URL, paste code - works everywhere
```

### Option 3: Generate Token Locally, Copy to Server
```bash
# On your local machine
git clone <repo>
cd gmail-fetcher
./setup-oauth.sh

# Copy token to server
scp data/token.json user@remote-host:/path/to/gmail-fetcher/data/

# Or if using Docker volume
scp data/token.json user@remote-host:/media/12TB/backup/gmail_data/
```

## Troubleshooting

### "Couldn't sign you in" / No JavaScript Error

You're seeing a text browser (w3m) trying to render the OAuth page.

**Solution**: Use `--no-auth-browser` flag for manual code entry.

### "Permission denied: /data"

You're running locally but it's trying to use container path.

**Solution**: The script now auto-detects and uses `./data` when running locally.

### "Redirect URI mismatch"

**Solution**: Add `http://localhost` to authorized redirect URIs in Google Cloud Console.

### Token expired or invalid

Delete the token and re-authenticate:
```bash
rm data/token.json
python gmail-fetcher.py --no-auth-browser
```

### Can't find credentials.json

**Solution**: Download from Google Cloud Console and save as `secrets/credentials.json`

## Security Notes

- ✅ Token stored locally in `data/token.json`
- ✅ Never commit `token.json` or `credentials.json` (.gitignore protects you)
- ✅ Token grants access to YOUR Gmail only
- ✅ Can revoke anytime at https://myaccount.google.com/permissions
- ✅ No third-party access - direct to Google APIs

## Token File Location

### Local Development
```
./data/token.json
```

### Docker Container
```
/data/token.json (mounted from host)
```

Either:
- `/media/12TB/backup/gmail_data/token.json` (default)
- `./data/token.json` (if using local mount)

## Re-authentication

You'll need to re-authenticate if:
- You revoke access at Google
- Token expires (refresh usually automatic)
- You delete `token.json`
- You change Gmail accounts

Just run the OAuth flow again - it's quick!

---

**Questions?** Check README.md or open an issue.
