# Headless Mode and Status Monitoring

Gmail Fetcher supports headless mode for Docker/cron/background operations, with status file output for monitoring via powerline, tmux, or scripts.

## Headless Mode

Perfect for:
- Docker containers
- Cron jobs
- Background processes
- Automated backups
- Servers without TTY

### Usage

```bash
# Headless with default status file
python gmail-fetcher.py --headless

# Custom status file location
python gmail-fetcher.py --headless --status-file /data/status.json

# Docker (default in docker-compose.yml)
docker compose up
```

### Status File

Status is written to JSON file (default: `/tmp/gmail-fetcher-status.json`):

```json
{
  "status": "running",
  "timestamp": "2025-11-17T10:30:45.123456",
  "stats": {
    "total_emails": 1000,
    "downloaded_emails": 450,
    "total_attachments": 120,
    "total_size_bytes": 52428800,
    "errors": 0,
    "rate_limit_hits": 0,
    "retries": 2
  },
  "config": {
    "query": "in:anywhere",
    "output_dir": "/data/emails"
  }
}
```

### Status Values

- `starting` - OAuth complete, starting download
- `running` - Actively downloading
- `complete` - Download finished successfully
- `error` - Fatal error occurred

## Status Monitoring

### Command Line

```bash
# Read current status
bin/gmail-status

# Output: 📧 450/1000 (45%)
```

### Formats

```bash
# Powerline format (for status bars)
bin/gmail-status --format powerline
# Output: 📧 450/1000 (45%)

# JSON format (for scripts)
bin/gmail-status --format json
# Output: Full JSON data

# Simple text format
bin/gmail-status --format simple
# Output:
# Gmail Fetcher: running
#   Downloaded: 450/1000
#   Size: 50.0 MB
#   Errors: 0
```

### Custom Status File

```bash
# If using custom location
bin/gmail-status --file /data/status.json
```

## Powerline Integration

### Powerline Shell

Add to `~/.config/powerline-shell/config.json`:

```json
{
  "segments": [
    "virtual_env",
    "cwd",
    {
      "type": "shell",
      "command": "/path/to/gmail-fetcher/bin/gmail-status"
    },
    "git"
  ]
}
```

### Tmux Status Bar

Add to `~/.tmux.conf`:

```bash
set -g status-right '#(/path/to/gmail-fetcher/bin/gmail-status) | %H:%M'
```

Reload tmux:
```bash
tmux source-file ~/.tmux.conf
```

### Oh My Zsh Custom Plugin

Create `~/.oh-my-zsh/custom/plugins/gmail-fetcher/gmail-fetcher.plugin.zsh`:

```bash
gmail_status() {
  /path/to/gmail-fetcher/bin/gmail-status
}

# Add to right prompt
RPS1='$(gmail_status) $RPS1'
```

Enable in `~/.zshrc`:
```bash
plugins=(... gmail-fetcher)
```

## Docker Usage

### docker-compose.yml (Default)

```yaml
services:
  gmail-fetcher:
    command: ["--headless", "--status-file", "/data/status.json"]
    volumes:
      - ./data:/data
```

Status file will be at: `./data/status.json`

### Read Status from Host

```bash
# While container is running
bin/gmail-status --file ./data/status.json

# Watch in real-time
watch -n 2 bin/gmail-status --file ./data/status.json
```

### Docker with Dashboard (Interactive)

```bash
# Override command for dashboard
docker compose run --rm gmail-fetcher --dash
```

**Note**: Dashboard requires TTY, so `docker compose up` won't show it properly. Use `docker compose run` with TTY.

## Cron Integration

### Example Crontab

```bash
# Weekly backup, Sunday 2 AM
0 2 * * 0 cd /path/to/gmail-fetcher && docker compose up > /var/log/gmail-fetcher.log 2>&1

# Check status every 5 minutes while running
*/5 * * * * /path/to/gmail-fetcher/bin/gmail-status --format simple >> /var/log/gmail-status.log
```

### With Notifications

```bash
#!/bin/bash
# cron-gmail-backup.sh

cd /path/to/gmail-fetcher
docker compose up

# Check final status
STATUS=$(bin/gmail-status --file data/status.json --format json | jq -r '.status')
ERRORS=$(bin/gmail-status --file data/status.json --format json | jq -r '.stats.errors')

if [ "$STATUS" = "complete" ] && [ "$ERRORS" -eq 0 ]; then
    echo "Gmail backup completed successfully" | mail -s "Backup Success" admin@example.com
else
    echo "Gmail backup had errors: $ERRORS" | mail -s "Backup Warning" admin@example.com
fi
```

## Monitoring Scripts

### Check if Running

```bash
#!/bin/bash
# is-gmail-fetcher-running.sh

STATUS_FILE="/data/status.json"

if [ ! -f "$STATUS_FILE" ]; then
    echo "Not running"
    exit 1
fi

# Check if file modified in last 5 minutes
if [ $(find "$STATUS_FILE" -mmin -5 | wc -l) -eq 0 ]; then
    echo "Stale (not running)"
    exit 1
fi

STATUS=$(jq -r '.status' "$STATUS_FILE")
if [ "$STATUS" = "running" ]; then
    echo "Running"
    exit 0
else
    echo "Not running (status: $STATUS)"
    exit 1
fi
```

### Progress Bar Script

```bash
#!/bin/bash
# gmail-progress.sh

STATUS_FILE="/data/status.json"

while true; do
    if [ -f "$STATUS_FILE" ]; then
        DATA=$(cat "$STATUS_FILE")
        STATUS=$(echo "$DATA" | jq -r '.status')
        DOWNLOADED=$(echo "$DATA" | jq -r '.stats.downloaded_emails')
        TOTAL=$(echo "$DATA" | jq -r '.stats.total_emails')

        if [ "$TOTAL" -gt 0 ]; then
            PERCENT=$((DOWNLOADED * 100 / TOTAL))
            echo -ne "Progress: $DOWNLOADED/$TOTAL ($PERCENT%) \\r"
        else
            echo -ne "Downloaded: $DOWNLOADED\\r"
        fi

        if [ "$STATUS" = "complete" ]; then
            echo ""
            echo "Complete!"
            break
        fi
    fi

    sleep 2
done
```

## API Access (Future)

Future versions may include:
- HTTP API endpoint for remote monitoring
- WebSocket for real-time updates
- Prometheus metrics export

## Troubleshooting

### Status file not updating

Check permissions:
```bash
ls -la /tmp/gmail-fetcher-status.json
chmod 644 /tmp/gmail-fetcher-status.json
```

### Stale status

Status files older than 5 minutes are considered stale and ignored by `gmail-status`.

### Permission denied

For Docker:
```yaml
volumes:
  - ./data:/data
# Status file at: ./data/status.json (accessible from host)
```

### Status shows nothing

```bash
# Check if process is running
ps aux | grep gmail-fetcher

# Check logs
docker compose logs
```

---

**Examples in action:**

```bash
# Terminal 1: Run in headless mode
docker compose up

# Terminal 2: Monitor status
watch -n 1 'bin/gmail-status --format simple'

# Terminal 3: Check raw JSON
cat data/status.json | jq .
```
