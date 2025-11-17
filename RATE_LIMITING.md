# Rate Limiting and API Quotas

## Gmail API Quotas

Google imposes the following quotas on the Gmail API:

| Quota | Limit | Notes |
|-------|-------|-------|
| **Queries per minute per user** | 15,000 | = 250 req/sec |
| **Queries per minute (project-wide)** | 1,200,000 | Shared across all users |
| **Queries per day** | 1,000,000,000 | Very unlikely to hit |

**Source**: [Gmail API Usage Limits](https://developers.google.com/gmail/api/reference/quota)

## How Gmail Fetcher Handles Rate Limits

### 1. Proactive Rate Limiting

Gmail Fetcher implements **client-side rate limiting** to prevent hitting API quotas:

```python
REQUESTS_PER_SECOND=10  # Default: 10 req/sec
```

This ensures:
- Controlled request rate
- Predictable behavior
- No quota exhaustion
- Respectful API usage

### 2. Exponential Backoff

If a rate limit error (HTTP 429) occurs, the client automatically:

1. **Retries** with exponential backoff: 1s → 2s → 4s → 8s → 16s
2. **Adds jitter** to prevent thundering herd
3. **Logs warnings** about rate limit hits
4. **Tracks statistics** (visible in dashboard)

### 3. Server Error Handling

Also retries on server errors (500, 503) with same exponential backoff strategy.

## Configuration

### Conservative (Default)
```bash
REQUESTS_PER_SECOND=10
MAX_RETRIES=5
```

**Use when**:
- Running multiple instances
- Sharing API project with others
- Being cautious
- First-time setup

**Performance**: ~600 emails/minute + attachment download time

### Moderate
```bash
REQUESTS_PER_SECOND=25
MAX_RETRIES=5
```

**Use when**:
- Personal single-user project
- Want faster downloads
- Moderate-sized archive

**Performance**: ~1,500 emails/minute + attachment download time

### Aggressive
```bash
REQUESTS_PER_SECOND=50
MAX_RETRIES=5
```

**Use when**:
- Dedicated API project
- Large archive to download
- Time is critical

**Performance**: ~3,000 emails/minute + attachment download time

### Maximum (Not Recommended)
```bash
REQUESTS_PER_SECOND=100
MAX_RETRIES=10
```

**Use when**:
- You know what you're doing
- Dedicated project quota
- Willing to risk rate limit errors

**Performance**: May hit rate limits depending on attachment sizes

### Disabled (Not Recommended)
```bash
REQUESTS_PER_SECOND=0
MAX_RETRIES=5
```

**Use when**:
- Testing
- You have other rate limiting in place

**Warning**: Will likely hit rate limits on large downloads

## Real-World Performance

Actual download speed depends on:

1. **Network latency**: API response time
2. **Email size**: Larger emails take longer
3. **Attachment size**: Large attachments slow downloads
4. **Concurrent operations**: Each email requires 1-2 API calls

### Example: 10,000 Emails

| Rate Limit | Est. Time | Notes |
|------------|-----------|-------|
| 10 req/sec | ~30 min | Conservative, no rate limit risk |
| 25 req/sec | ~12 min | Good balance |
| 50 req/sec | ~6 min | Fast, low risk |
| 100 req/sec | ~4 min | May hit limits |

*Plus attachment download time (varies)*

## Monitoring Rate Limits

### Dashboard Display

When using `--dash`, rate limit stats are shown:

```
Statistics
├─ Rate Limits Hit: 2
└─ API Retries: 5
```

### Log Messages

```
WARNING - Rate limit hit on get message abc12345. Retrying in 2.3s (attempt 2/5)
WARNING - Server error 503 on list messages. Retrying in 4.1s (attempt 3/5)
```

## Troubleshooting

### Getting Rate Limited?

**Symptoms**:
- Warnings about rate limit hits
- Slow downloads
- HTTP 429 errors

**Solutions**:
1. Decrease `REQUESTS_PER_SECOND`
2. Increase `MAX_RETRIES`
3. Check if other apps are using the same API project
4. Wait for quota reset (per minute)

### Too Slow?

**Symptoms**:
- Downloads taking too long
- No rate limit warnings

**Solutions**:
1. Increase `REQUESTS_PER_SECOND` (try 25 or 50)
2. Check network latency
3. Consider running during off-peak hours
4. Profile to see if it's attachment download time

### Exponential Backoff Not Working?

**Symptoms**:
- Immediate failures
- No retry attempts

**Check**:
1. `MAX_RETRIES` > 0
2. Logs show retry attempts
3. Error is actually 429/500/503 (other errors don't retry)

## API Call Breakdown

### Per Email Download:

1. **List messages** (1 call per 500 emails)
2. **Get message detail** (1 call per email)
3. **Get attachment** (1 call per attachment, if needed)

### Example: 1,000 Emails with Attachments

- List: ~2 calls (500 per page)
- Get: 1,000 calls
- Attachments: ~500 calls (avg 0.5 per email)
- **Total**: ~1,502 API calls

At 10 req/sec: ~150 seconds = 2.5 minutes (just API calls)

## Best Practices

1. **Start Conservative**: Use default 10 req/sec initially
2. **Monitor First Run**: Watch dashboard for rate limit hits
3. **Increase Gradually**: If no issues, try 25 → 50
4. **Test with Limits**: Use `MAX_RESULTS=100` for testing
5. **Respect Quotas**: Don't disable rate limiting
6. **Check Logs**: Review for patterns of rate limit errors
7. **Consider Time**: Large downloads can run overnight

## Quota Management

### Checking Your Quota Usage

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project
3. Navigate to "APIs & Services" > "Dashboard"
4. Click "Gmail API"
5. View quota usage graphs

### Requesting Quota Increase

For enterprise/heavy use:
1. Go to "IAM & Admin" > "Quotas"
2. Filter for "Gmail API"
3. Select quota to increase
4. Click "Edit Quotas"
5. Provide justification

**Note**: Increases are rarely needed for personal use

## Technical Details

### Rate Limiter Implementation

Uses **token bucket algorithm**:
```python
class RateLimiter:
    def __init__(self, requests_per_second: float):
        self.min_interval = 1.0 / requests_per_second

    def wait_if_needed(self):
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request_time = time.time()
```

### Exponential Backoff Implementation

```python
for attempt in range(max_retries + 1):
    try:
        return request.execute()
    except HttpError as error:
        if error.resp.status in [429, 500, 503]:
            delay = base_delay * (2 ** attempt)
            delay = delay * (0.5 + random.random())  # Jitter
            time.sleep(delay)
            continue
        raise
```

## FAQ

**Q: Will I hit rate limits with default settings?**
A: Very unlikely. Default 10 req/sec is 4% of the quota.

**Q: Can I set REQUESTS_PER_SECOND higher than 250?**
A: Yes, but it won't go faster - Gmail limits to 250/sec.

**Q: What happens if I exceed quota?**
A: You get HTTP 429 errors, which trigger exponential backoff.

**Q: Does rate limiting slow downloads significantly?**
A: At 10 req/sec, minimal impact. At 50 req/sec, negligible.

**Q: Should I disable rate limiting for speed?**
A: No - you'll hit quotas and get blocked longer by backoff.

**Q: How do I calculate optimal rate limit?**
A: Start at 10, double if no rate limit hits, halve if you get them.

**Q: Does this affect OAuth or authentication?**
A: No - rate limiting only applies to email fetching operations.

---

**Bottom Line**: The default settings (10 req/sec, 5 retries) work well for most users. Increase to 25-50 for faster downloads if you're not hitting limits.
