# Gmail Fetcher Monitoring Examples

Quick reference for monitoring Gmail Fetcher in headless mode.

## Basic Monitoring

### One-time Status Check

```bash
# Powerline format (concise, perfect for status bars)
bin/gmail-status --file /media/12TB/backup/gmail_data/status.json
# Output: 📧 313

# Simple format (detailed, human-readable)
bin/gmail-status --file /media/12TB/backup/gmail_data/status.json --format simple
# Output:
# Gmail Fetcher: running
#   Downloaded: 313
#   Size: 8.5 MB
#   Errors: 0

# JSON format (for scripting)
bin/gmail-status --file /media/12TB/backup/gmail_data/status.json --format json | jq '.stats'
```

### Real-time Monitoring

```bash
# Watch command (updates every 2 seconds)
watch -n 2 'bin/gmail-status --file /media/12TB/backup/gmail_data/status.json --format simple'

# Loop with custom interval
while true; do
    clear
    bin/gmail-status --file /media/12TB/backup/gmail_data/status.json --format simple
    sleep 5
done
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
      "command": "/media/4TB/git_repos/gmail-fetcher/bin/gmail-status --file /media/12TB/backup/gmail_data/status.json"
    },
    "git"
  ]
}
```

### Tmux Status Bar

Add to `~/.tmux.conf`:

```bash
set -g status-right '#(/media/4TB/git_repos/gmail-fetcher/bin/gmail-status --file /media/12TB/backup/gmail_data/status.json) | %H:%M'
```

Reload: `tmux source-file ~/.tmux.conf`

### Oh My Zsh Plugin

Create `~/.oh-my-zsh/custom/plugins/gmail-fetcher/gmail-fetcher.plugin.zsh`:

```bash
gmail_status() {
  /media/4TB/git_repos/gmail-fetcher/bin/gmail-status --file /media/12TB/backup/gmail_data/status.json
}

# Add to right prompt
RPS1='$(gmail_status) $RPS1'
```

Enable in `~/.zshrc`:
```bash
plugins=(... gmail-fetcher)
```

## Scripting Examples

### Check if Download is Complete

```bash
#!/bin/bash
STATUS=$(bin/gmail-status --file /media/12TB/backup/gmail_data/status.json --format json | jq -r '.status')

if [ "$STATUS" = "complete" ]; then
    echo "Download finished!"
    # Your post-download actions here
else
    echo "Still running..."
fi
```

### Email Notification on Completion

```bash
#!/bin/bash
while true; do
    STATUS=$(bin/gmail-status --file /media/12TB/backup/gmail_data/status.json --format json | jq -r '.status')

    if [ "$STATUS" = "complete" ]; then
        DOWNLOADED=$(bin/gmail-status --file /media/12TB/backup/gmail_data/status.json --format json | jq -r '.stats.downloaded_emails')
        SIZE=$(bin/gmail-status --file /media/12TB/backup/gmail_data/status.json --format json | jq -r '.stats.total_size_bytes')
        SIZE_MB=$((SIZE / 1024 / 1024))

        echo "Gmail backup complete: $DOWNLOADED emails, ${SIZE_MB}MB" | \
            mail -s "Gmail Backup Complete" your@email.com
        break
    fi

    sleep 60
done
```

### Progress Bar

```bash
#!/bin/bash
while true; do
    DATA=$(bin/gmail-status --file /media/12TB/backup/gmail_data/status.json --format json)
    STATUS=$(echo "$DATA" | jq -r '.status')
    DOWNLOADED=$(echo "$DATA" | jq -r '.stats.downloaded_emails')
    SIZE=$(echo "$DATA" | jq -r '.stats.total_size_bytes')
    SIZE_MB=$((SIZE / 1024 / 1024))

    echo -ne "📧 Downloaded: $DOWNLOADED emails | Size: ${SIZE_MB}MB\r"

    if [ "$STATUS" = "complete" ]; then
        echo ""
        echo "✅ Complete!"
        break
    fi

    sleep 2
done
```

## Cron Integration

### Weekly Backup with Notification

```bash
# crontab -e
# Every Sunday at 2 AM
0 2 * * 0 /media/4TB/git_repos/gmail-fetcher/cron-backup.sh
```

Create `cron-backup.sh`:

```bash
#!/bin/bash
cd /media/4TB/git_repos/gmail-fetcher

# Run backup
docker compose up

# Check result
STATUS=$(bin/gmail-status --file /media/12TB/backup/gmail_data/status.json --format json | jq -r '.status')
ERRORS=$(bin/gmail-status --file /media/12TB/backup/gmail_data/status.json --format json | jq -r '.stats.errors')

if [ "$STATUS" = "complete" ] && [ "$ERRORS" -eq 0 ]; then
    echo "Gmail backup completed successfully" | mail -s "Backup Success" admin@example.com
else
    echo "Gmail backup had $ERRORS errors" | mail -s "Backup Warning" admin@example.com
fi
```

## Container Management

### Run in Background

```bash
# Start in background
docker compose up -d

# Monitor status
watch -n 2 'bin/gmail-status --file /media/12TB/backup/gmail_data/status.json'

# Check logs
docker compose logs -f

# Stop gracefully
docker compose down
```

### Interactive Dashboard Mode

If you prefer the visual dashboard:

```bash
# Override command for dashboard
docker compose run --rm gmail-fetcher --dash
```

Note: Dashboard requires TTY, so use `docker compose run` instead of `docker compose up`.

## API Usage Example

Parse JSON for custom integrations:

```bash
# Get specific fields
DOWNLOADED=$(bin/gmail-status --file /media/12TB/backup/gmail_data/status.json --format json | jq -r '.stats.downloaded_emails')
TOTAL=$(bin/gmail-status --file /media/12TB/backup/gmail_data/status.json --format json | jq -r '.stats.total_emails')
ERRORS=$(bin/gmail-status --file /media/12TB/backup/gmail_data/status.json --format json | jq -r '.stats.errors')
SIZE=$(bin/gmail-status --file /media/12TB/backup/gmail_data/status.json --format json | jq -r '.stats.total_size_bytes')

# Calculate percentage if total is known
if [ "$TOTAL" -gt 0 ]; then
    PERCENT=$((DOWNLOADED * 100 / TOTAL))
    echo "Progress: $PERCENT%"
fi

# Check for errors
if [ "$ERRORS" -gt 0 ]; then
    echo "Warning: $ERRORS errors occurred"
fi
```

## Troubleshooting

### Status Not Updating

Check file modification time:
```bash
stat /media/12TB/backup/gmail_data/status.json
```

Status files older than 5 minutes are considered stale.

### Permission Issues

Ensure the status file is readable:
```bash
ls -la /media/12TB/backup/gmail_data/status.json
chmod 644 /media/12TB/backup/gmail_data/status.json  # if needed
```

### Container Not Running

Check container status:
```bash
docker compose ps
docker compose logs
```

---

**See also:**
- [docs/headless-mode.md](docs/headless-mode.md) - Full headless mode documentation
- [README.md](README.md) - Main documentation
- [RATE_LIMITING.md](RATE_LIMITING.md) - Rate limiting configuration
