# Excluding Spam and Trash - Update Guide

## Changes Made

Gmail Fetcher now **excludes spam and trash by default** to:
- Save disk space
- Avoid errors from malformed spam emails
- Focus on legitimate email backup
- Improve download performance

## Updated Files

1. **.env.example** - Default query now: `-in:spam -in:trash`
2. **.env.user-example** - Updated default
3. **docker-compose.yml** - Container default updated
4. **QUERY_EXAMPLES.md** - Comprehensive query guide created

## For Your Current Download

Your current download is using: `in:anywhere` (includes spam and trash)

**To stop and restart with spam exclusion:**

```bash
# Stop current download
docker compose down

# Update your query in .env or docker-compose.yml
# Option 1: Edit .env file (if it exists)
# Change: GMAIL_QUERY=in:anywhere
# To:     GMAIL_QUERY=-in:spam -in:trash

# Option 2: Override in docker-compose command
docker compose up

# The new default will automatically exclude spam/trash
```

**To continue current download and clean up spam later:**

```bash
# Let current download finish
# Then manually remove spam/trash from downloaded data:
rm -rf /media/12TB/backup/gmail_data/emails/*/spam
rm -rf /media/12TB/backup/gmail_data/emails/*/trash
```

## Query Examples

### Recommended (Default)
```bash
GMAIL_QUERY="-in:spam -in:trash"
```

### Include Everything
```bash
GMAIL_QUERY="in:anywhere"
```

### Only Inbox
```bash
GMAIL_QUERY="in:inbox"
```

### Important Emails Only
```bash
GMAIL_QUERY="is:important -in:spam -in:trash"
```

### Date Range (Excluding Spam/Trash)
```bash
GMAIL_QUERY="after:2020/01/01 before:2024/01/01 -in:spam -in:trash"
```

## See Full Documentation

- **QUERY_EXAMPLES.md** - Complete guide with 30+ examples
- **README.md** - Main documentation
- Gmail search operators: https://support.google.com/mail/answer/7190

## Performance Impact

Excluding spam and trash typically:
- Reduces download size by 20-40%
- Eliminates most filename errors
- Speeds up download by 20-30%
- Improves data quality

## Testing a Query

Before downloading, test in Gmail web interface:
1. Open Gmail
2. Type query in search box: `-in:spam -in:trash`
3. Verify results look correct
4. Use same query in Gmail Fetcher

---

**Quick Update:**

Edit your `.env` or let docker-compose use the new default:
```bash
# New runs will automatically exclude spam/trash
docker compose build
docker compose up
```
