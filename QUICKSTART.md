# Quick Start Guide

Get up and running with Gmail Fetcher in 5 minutes!

## Prerequisites

- Docker and Docker Compose installed
- Gmail account
- 5 minutes

## Step-by-Step

### 1. Get Gmail API Credentials

Visit [Google Cloud Console](https://console.cloud.google.com/):

1. Create a new project
2. Enable "Gmail API"
3. Create "OAuth client ID" credentials
4. Choose "Desktop app"
5. Download JSON file

### 2. Run Setup Script

```bash
./setup.sh
```

This will:
- Create required directories
- Copy your credentials
- Configure settings interactively
- Build the Docker image

### 3. Run!

```bash
make run
```

Or manually:
```bash
docker-compose up
```

### 4. First-Time OAuth

1. A URL will appear in the terminal
2. Open it in your browser
3. Log in to Gmail
4. Authorize the app
5. Copy the code back to the terminal

Done! Your emails will start downloading.

## What You Get

```
data/
└── emails/
    └── 2024/
        └── 11/
            └── 17/
                └── 143022_Important_Email_abc12345/
                    ├── metadata.json
                    ├── body.html
                    └── attachments/
                        └── document.pdf
```

## Common Commands

```bash
# Run with dashboard
make run

# Run in batch mode (no UI)
make run-batch

# View logs
make logs

# Clean downloaded emails
make clean

# Check security
make security-check

# Get help
make help
```

## Configuration

Edit `.env` file:

```bash
# Download only emails with attachments
GMAIL_QUERY=has:attachment

# Limit to 100 emails
MAX_RESULTS=100

# Enable encrypted archives
ARCHIVE_ENABLED=true
```

## Troubleshooting

**Can't authenticate?**
- Make sure credentials.json is in `secrets/` directory
- Check file permissions: `chmod 600 secrets/credentials.json`

**Container exits immediately?**
- Run `docker-compose logs` to see errors
- Check `.env` configuration
- Verify credentials.json is valid JSON

**Permission denied?**
- Run `make security-check` to fix permissions
- Or manually: `chmod 700 secrets data`

**Want to run locally for OAuth?**
```bash
# Install uv (fast Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Quick setup
uv venv && uv pip install -r requirements.txt
source .venv/bin/activate
cp secrets/credentials.json .
python gmail-fetcher.py --dash

# Token will be saved to token.json
# Copy to container: cp token.json /media/12TB/backup/gmail_data/
```

## Next Steps

- Read [README.md](README.md) for full documentation
- Review [SECURITY.md](SECURITY.md) for security best practices
- Check [RATE_LIMITING.md](RATE_LIMITING.md) to optimize download speed
- Customize your Gmail query
- Set up scheduled backups

## Need Help?

- Run `make help` for available commands
- Check logs: `docker-compose logs`
- Review error messages carefully
- Ensure Docker is running: `docker ps`

---

**Pro Tips:**

- Test with a small query first: `GMAIL_QUERY="from:me" MAX_RESULTS=10`
- Use `--dash` flag for a nice terminal UI
- Keep your `token.json` safe - it grants Gmail access
- Never use `DELETE_AFTER_DOWNLOAD=true` without testing first!
