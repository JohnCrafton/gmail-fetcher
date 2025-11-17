# Gmail Fetcher

> **NOTE**:  Created largely by Claude based on prompting and online examples.  Auditing has not yet taken place.  This message is generated as part of the project automation and should not be removed.

A **secure, local** Gmail archiving solution designed to run in a distroless Docker container. Download your entire Gmail account including attachments, with optional encryption and archiving.

## Security Features

This project prioritizes security and transparency:

- **Non-Root User**: Container runs as non-root user - never as root
- **PUID/PGID Support**: Set file ownership to match your user (e.g., 1000:1000) for easy access
- **Two Security Modes**: Choose between flexible (PUID/PGID) or distroless (maximum security)
- **Docker Secrets**: Credentials stored as Docker secrets, not environment variables
- **No Privilege Escalation**: Security option `no-new-privileges` prevents privilege escalation
- **Minimal Capabilities**: All Linux capabilities dropped
- **Local Storage Only**: No cloud uploads - everything stays on your machine
- **Resource Limits**: CPU and memory limits prevent resource exhaustion
- **Encrypted Archives**: Optional password-protected 7z archives with AES-256 encryption
- **OAuth2 Flow**: Uses official Google OAuth2 (no password storage)
- **Transparent Code**: All source code is included and readable

> **Note**: Default mode uses `python:slim` base for PUID/PGID flexibility. For maximum security (distroless, no shell), use `make run-distroless`. See [DEPLOYMENT_MODES.md](DEPLOYMENT_MODES.md) for details.

## Features

- Download all emails from Gmail with customizable queries
- Save email bodies (text/HTML) and attachments
- Organize emails by date (year/month/day) with safe filenames
- Optional terminal dashboard interface (like k9s)
- **Built-in rate limiting** with exponential backoff (respects Gmail API quotas)
- Create encrypted archive of downloaded emails
- Batch mode or interactive mode
- Comprehensive logging
- Configurable via environment variables or .env file

## Prerequisites

- Docker and Docker Compose
- Gmail account with API access enabled
- Gmail API credentials (see setup below)

## Quick Start

### 1. Get Gmail API Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Gmail API:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Gmail API"
   - Click "Enable"
4. Create OAuth2 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Desktop app" as application type
   - Download the JSON file
5. Save as `secrets/credentials.json` in this repo

### 2. Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd gmail-fetcher

# Create required directories
mkdir -p secrets data

# Copy credentials
cp ~/Downloads/client_secret_*.json secrets/credentials.json

# Create .env file from example
cp .env.example .env

# Set your user's UID/GID for file ownership (optional but recommended)
echo "PUID=$(id -u)" >> .env
echo "PGID=$(id -g)" >> .env

# (Optional) Set archive password for encrypted backups
echo "your-strong-password" > secrets/archive_password.txt

# Set proper permissions (important!)
chmod 600 secrets/credentials.json
chmod 600 .env
chmod 700 secrets
```

### 3. Configure

Edit `.env` to customize your download settings:

```bash
# Example: Download all emails from a specific sender
GMAIL_QUERY=from:important@example.com

# Example: Download emails from last year
GMAIL_QUERY=after:2023/01/01 before:2024/01/01

# Enable archiving
ARCHIVE_ENABLED=true
```

See [Gmail Search Operators](https://support.google.com/mail/answer/7190) for query syntax.

### 4. Run

**Headless mode (default, best for Docker):**
```bash
docker-compose up
# Status written to data/status.json
# Monitor with: bin/gmail-status --file data/status.json
```

**With Dashboard (interactive, requires TTY):**
```bash
docker-compose run --rm gmail-fetcher --dash
```

**Batch mode (logs only):**
```bash
docker-compose run --rm gmail-fetcher
```

**Custom query:**
```bash
GMAIL_QUERY="has:attachment after:2024/01/01" docker-compose up
```

### 5. First Run - OAuth Setup

**Easy way:**
```bash
./setup-oauth.sh
```

**Manual way:**
```bash
# Install dependencies locally
uv venv && uv pip install -r requirements.txt
source .venv/bin/activate

# Run OAuth flow
python gmail-fetcher.py --no-auth-browser
```

Follow the prompts to authorize Gmail access. See [QUICKSTART_OAUTH.md](QUICKSTART_OAUTH.md) for detailed instructions.

Token is saved to `data/token.json` - you won't need to re-authenticate unless you revoke access.

## Dashboard Interface

When run with `--dash` flag (default in docker-compose), you get a beautiful terminal interface showing:

- Real-time download progress
- Email and attachment counts
- Total data size
- Download speed
- Error tracking
- Configuration display
- Security status indicators

## Directory Structure

```
gmail-fetcher/
├── src/                    # Application source code
│   ├── __init__.py
│   ├── main.py            # Main entry point
│   ├── config.py          # Configuration management
│   ├── gmail_client.py    # Gmail API client
│   ├── downloader.py      # Email download logic
│   ├── archiver.py        # Archive creation
│   └── dashboard.py       # Terminal UI
├── secrets/               # Docker secrets (gitignored)
│   ├── credentials.json   # Gmail API credentials
│   └── archive_password.txt  # Archive password
├── data/                  # Downloaded emails (gitignored)
│   ├── token.json         # OAuth token (auto-generated)
│   └── emails/            # Downloaded emails
│       └── 2024/
│           └── 01/
│               └── 15/
│                   └── 120530_Email_Subject_abc12345/
│                       ├── metadata.json
│                       ├── body.html
│                       └── attachments/
├── Dockerfile             # Distroless container definition
├── docker-compose.yml     # Orchestration with secrets
├── requirements.txt       # Python dependencies
├── .env.example           # Example configuration
└── README.md             # This file
```

## Configuration Reference

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PUID` | `65532` | User ID for file ownership (use `id -u` to find yours) |
| `PGID` | `65532` | Group ID for file ownership (use `id -g` to find yours) |
| `GMAIL_QUERY` | `in:anywhere` | Gmail search query |
| `MAX_RESULTS` | `0` | Max emails to download (0 = unlimited) |
| `INCLUDE_ATTACHMENTS` | `true` | Download attachments |
| `DELETE_AFTER_DOWNLOAD` | `false` | ⚠️ Delete emails after download |
| `REQUESTS_PER_SECOND` | `10` | API rate limit (max 250, recommended 10-50) |
| `MAX_RETRIES` | `5` | Retry attempts for rate limit/server errors |
| `ARCHIVE_ENABLED` | `false` | Create archive after download |
| `ARCHIVE_PASSWORD` | - | Password for encrypted archive |
| `DATA_DIR` | `/data` | Output directory |
| `CREDENTIALS_PATH` | `/run/secrets/gmail_credentials` | Path to credentials |

**Tips**:
- Set `PUID=1000` and `PGID=1000` (or your user's ID) to own downloaded files without needing sudo
- Default rate limit (10 req/sec) is conservative; increase to 25-50 for faster downloads
- Gmail API allows up to 250 req/sec per user and 15,000 req/min

### Gmail Query Examples

```bash
# All emails
GMAIL_QUERY="in:anywhere"

# Emails with attachments
GMAIL_QUERY="has:attachment"

# From specific sender
GMAIL_QUERY="from:boss@company.com"

# Date range
GMAIL_QUERY="after:2020/01/01 before:2023/12/31"

# Unread emails
GMAIL_QUERY="is:unread"

# Large emails (>5MB)
GMAIL_QUERY="size:5000000"

# Combine conditions
GMAIL_QUERY="from:john@example.com has:attachment after:2024/01/01"
```

## Security Considerations

### What This Does

- ✅ Runs in isolated, minimal container
- ✅ Stores credentials as Docker secrets
- ✅ Never runs as root
- ✅ Uses official Google OAuth2 flow
- ✅ Keeps all data local
- ✅ Encrypts archives with AES-256
- ✅ Provides full source code transparency
- ✅ Logs all operations

### What You Should Do

1. **Never commit credentials**: The `.gitignore` is configured to prevent this, but always double-check
2. **Rotate credentials regularly**: Revoke and recreate API credentials periodically
3. **Use strong archive passwords**: If archiving, use a password manager
4. **Review permissions**: Check what permissions the OAuth flow requests
5. **Monitor logs**: Review logs for any unexpected behavior
6. **Backup token.json**: Store it securely if you don't want to re-authenticate
7. **Test before DELETE**: Never use `DELETE_AFTER_DOWNLOAD=true` without testing first
8. **Limit scope**: Use specific queries instead of downloading everything
9. **Secure the host**: Ensure your Docker host is secure
10. **Check downloaded data**: Verify downloads before deleting originals

### Security Warnings

⚠️ **DELETE_AFTER_DOWNLOAD**: This permanently deletes emails from Gmail. Use with extreme caution!

⚠️ **Token Storage**: `token.json` grants access to your Gmail. Protect it like a password.

⚠️ **Archive Passwords**: Don't lose them - archives are AES-256 encrypted and cannot be recovered.

## Troubleshooting

### OAuth Browser Opens But Can't Connect

The container runs an HTTP server on a random port for the OAuth callback. If running on a remote host, you may need to:

```bash
# Use --no-auth-browser flag and manually copy the auth code
docker-compose run gmail-fetcher --no-auth-browser
```

### Permission Denied Errors

Ensure directories have correct permissions:
```bash
chmod 700 secrets data
chmod 600 secrets/credentials.json
```

### Container Exits Immediately

Check logs:
```bash
docker-compose logs
```

Common issues:
- Missing credentials.json
- Invalid .env configuration
- Missing archive password when archiving is enabled

### Out of Disk Space

Check disk usage and set `MAX_RESULTS`:
```bash
du -sh data/
```

Set a limit:
```bash
MAX_RESULTS=1000 docker-compose up
```

## Development

### Local Development (without Docker)

We use **uv** for fast, modern Python package management:

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
uv pip install -r requirements.txt

# Or install in editable mode
uv pip install -e .

# Activate environment
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows

# Copy credentials
cp ~/Downloads/client_secret_*.json credentials.json

# Run
python gmail-fetcher.py --dash
```

**Why uv?** It's 10-100x faster than pip and has better dependency resolution.

### Building the Container

```bash
# Build
docker build -t gmail-fetcher .

# Run
docker run -it --rm \
  -v $(pwd)/data:/data \
  -v $(pwd)/secrets/credentials.json:/run/secrets/gmail_credentials:ro \
  gmail-fetcher --dash
```

## Automated/Scheduled Runs

### Using Cron

Add to crontab for weekly backups:
```bash
# Every Sunday at 2 AM
0 2 * * 0 cd /path/to/gmail-fetcher && docker-compose run --rm gmail-fetcher
```

### Using Systemd Timer

Create `/etc/systemd/system/gmail-fetcher.service`:
```ini
[Unit]
Description=Gmail Fetcher
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
WorkingDirectory=/path/to/gmail-fetcher
ExecStart=/usr/bin/docker-compose run --rm gmail-fetcher
```

Create `/etc/systemd/system/gmail-fetcher.timer`:
```ini
[Unit]
Description=Run Gmail Fetcher weekly

[Timer]
OnCalendar=Sun *-*-* 02:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

Enable:
```bash
systemctl daemon-reload
systemctl enable --now gmail-fetcher.timer
```

## Contributing

This is a personal archiving tool, but contributions are welcome! Please ensure:

- Security best practices are maintained
- Code is well-documented
- No credentials or tokens in commits
- Tests pass (when implemented)

## License

MIT License - See LICENSE file for details

## Disclaimer

This tool is provided as-is for personal use. Always:

- Review code before running
- Test with small datasets first
- Never use DELETE_AFTER_DOWNLOAD without extensive testing
- Keep backups of important data
- Review Google's Terms of Service
- Understand OAuth2 permissions you're granting

The authors are not responsible for any data loss or security issues arising from use of this tool.

## Acknowledgments

- Inspired by [g-Downloader](https://github.com/rylaix/g-Downloader)
- Built with [Google Gmail API](https://developers.google.com/gmail/api)
- Terminal UI powered by [Rich](https://github.com/Textualize/rich)
- Container security using [Distroless](https://github.com/GoogleContainerTools/distroless)

---

**Questions or Issues?** Open an issue on GitHub or review the source code in `src/`.

**Built with security and transparency in mind. Inspect the code. Trust, but verify.**
