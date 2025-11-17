# Gmail Query Examples

Gmail Fetcher uses standard Gmail search syntax for filtering which emails to download.

## Recommended Default

**Exclude spam and trash** (saves space and avoids problematic emails):

```bash
GMAIL_QUERY="-in:spam -in:trash"
```

This is now the default in `.env.example` and `docker-compose.yml`.

## Common Query Patterns

### Exclude Folders

```bash
# Exclude spam and trash (recommended)
GMAIL_QUERY="-in:spam -in:trash"

# Exclude just spam
GMAIL_QUERY="-in:spam"

# Only inbox emails
GMAIL_QUERY="in:inbox"

# Everything (including spam/trash)
GMAIL_QUERY="in:anywhere"
```

### Filter by Sender

```bash
# From specific person
GMAIL_QUERY="from:john@example.com"

# From domain
GMAIL_QUERY="from:@company.com"

# Exclude sender
GMAIL_QUERY="-from:spam@example.com"
```

### Filter by Date

```bash
# Emails from 2023
GMAIL_QUERY="after:2023/01/01 before:2024/01/01"

# Last 6 months
GMAIL_QUERY="newer_than:6m"

# Older than 1 year
GMAIL_QUERY="older_than:1y"

# Specific year, excluding spam/trash
GMAIL_QUERY="after:2020/01/01 before:2021/01/01 -in:spam -in:trash"
```

### Filter by Content

```bash
# Has attachments
GMAIL_QUERY="has:attachment"

# Specific subject
GMAIL_QUERY="subject:invoice"

# Contains text
GMAIL_QUERY="password reset"

# Large emails (>5MB)
GMAIL_QUERY="larger:5M"

# Small emails (<1MB)
GMAIL_QUERY="smaller:1M"
```

### Filter by Status

```bash
# Unread emails
GMAIL_QUERY="is:unread"

# Starred emails
GMAIL_QUERY="is:starred"

# Important emails
GMAIL_QUERY="is:important"

# Read emails
GMAIL_QUERY="is:read"
```

### Filter by Labels

```bash
# Specific label
GMAIL_QUERY="label:receipts"

# Has any label
GMAIL_QUERY="has:userlabels"

# Multiple labels
GMAIL_QUERY="label:work label:important"
```

## Combining Filters

Use spaces to combine multiple conditions (AND logic):

```bash
# Important emails from 2023 with attachments, excluding spam
GMAIL_QUERY="is:important after:2023/01/01 before:2024/01/01 has:attachment -in:spam -in:trash"

# Emails from boss that are unread
GMAIL_QUERY="from:boss@company.com is:unread"

# Large attachments from this year
GMAIL_QUERY="has:attachment larger:10M after:2024/01/01 -in:spam"
```

Use OR for alternatives:

```bash
# From either sender
GMAIL_QUERY="from:alice@example.com OR from:bob@example.com"

# Either label
GMAIL_QUERY="label:work OR label:personal"
```

## Practical Examples

### Backup Important Mail Only

```bash
# Stars, important, or has attachments (excluding spam/trash)
GMAIL_QUERY="(is:starred OR is:important OR has:attachment) -in:spam -in:trash"
```

### Archive Project Emails

```bash
# Specific project from team members
GMAIL_QUERY="from:@company.com subject:ProjectX -in:spam -in:trash"
```

### Download Receipts

```bash
# Common receipt keywords with attachments
GMAIL_QUERY="(subject:receipt OR subject:invoice OR subject:order) has:attachment -in:spam -in:trash"
```

### Legal/Compliance Backup

```bash
# All business emails from date range
GMAIL_QUERY="from:@company.com after:2020/01/01 before:2023/12/31 -in:spam -in:trash"
```

### Media Archive

```bash
# Photos and videos
GMAIL_QUERY="(filename:jpg OR filename:png OR filename:mp4 OR filename:mov) -in:spam -in:trash"
```

### Incremental Backups

```bash
# Only emails newer than last backup
GMAIL_QUERY="after:2024/11/01 -in:spam -in:trash"
```

## Performance Tips

### Smaller, Focused Queries Are Faster

Instead of:
```bash
GMAIL_QUERY="in:anywhere"  # Downloads everything including spam
```

Use:
```bash
GMAIL_QUERY="-in:spam -in:trash"  # Skip folders you don't need
```

### Break Large Backups into Chunks

For huge mailboxes, download by year:

```bash
# Year 1
GMAIL_QUERY="after:2020/01/01 before:2021/01/01 -in:spam -in:trash"

# Year 2
GMAIL_QUERY="after:2021/01/01 before:2022/01/01 -in:spam -in:trash"
```

### Skip Large Attachments for Testing

```bash
# Test query without large files
GMAIL_QUERY="smaller:1M -in:spam -in:trash"
MAX_RESULTS=100
```

## Why Exclude Spam and Trash?

**Reasons to exclude spam/trash:**
1. **Space savings** - Spam is usually junk you don't need
2. **Fewer errors** - Spam often has malformed subjects/attachments
3. **Faster downloads** - Less data to process
4. **Better organization** - Focus on legitimate emails
5. **Security** - Avoid archiving potentially malicious content

**When you might want spam/trash:**
- Legal/compliance requirements
- Investigating phishing/spam patterns
- Complete account migration
- Training spam filters

To include everything:
```bash
GMAIL_QUERY="in:anywhere"
```

## Troubleshooting Queries

### Test Queries in Gmail First

Before downloading, test your query in Gmail's search box:
1. Open Gmail web interface
2. Type your query in the search box
3. Verify it returns the expected emails
4. Copy the exact query to `.env`

### Check Result Count

Use a small `MAX_RESULTS` for testing:

```bash
GMAIL_QUERY="your complex query here"
MAX_RESULTS=10  # Just download 10 to test
```

### View Query in Logs

The downloader logs the query being used:

```bash
docker compose logs | grep "Starting download with query"
```

## Reference

Full Gmail search operator documentation:
https://support.google.com/mail/answer/7190

---

**Quick Start:**

Most users should use:
```bash
GMAIL_QUERY="-in:spam -in:trash"
```

This is now the default in Gmail Fetcher!
