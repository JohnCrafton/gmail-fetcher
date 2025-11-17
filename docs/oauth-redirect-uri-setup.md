# Adding OAuth Redirect URI to Google Cloud Console

If you get an error like "missing required parameter: redirect_uri" or "redirect_uri_mismatch", you need to configure your OAuth client.

## Steps

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/
   - Select your project

2. **Navigate to Credentials**
   - Click "APIs & Services" in the left menu
   - Click "Credentials"

3. **Edit your OAuth 2.0 Client ID**
   - Find your OAuth 2.0 Client ID in the list
   - Click the pencil icon (✏️) to edit

4. **Add Authorized Redirect URIs**

   Add these three URIs:

   ```
   urn:ietf:wg:oauth:2.0:oob
   http://localhost
   http://127.0.0.1
   ```

   **What each one does:**
   - `urn:ietf:wg:oauth:2.0:oob` - For manual code flow (`--no-auth-browser`)
   - `http://localhost` - For local browser flow (automatic)
   - `http://127.0.0.1` - Alternative for local browser flow

5. **Save**
   - Click "Save" at the bottom

## Screenshot Guide

### Step 1: Find Credentials
```
APIs & Services → Credentials
```

### Step 2: Click Edit (Pencil Icon)
Look for your OAuth 2.0 Client ID and click the pencil.

### Step 3: Add Redirect URIs
Scroll down to "Authorized redirect URIs" section.

Click "+ ADD URI" for each one:
1. `urn:ietf:wg:oauth:2.0:oob`
2. `http://localhost`
3. `http://127.0.0.1`

### Step 4: Save
Click the "SAVE" button at the bottom.

## Common Issues

### "redirect_uri_mismatch" Error

**Problem**: The redirect URI in the OAuth flow doesn't match what's configured.

**Solution**: Make sure you added `urn:ietf:wg:oauth:2.0:oob` exactly as shown (no typos).

### "missing required parameter: redirect_uri"

**Problem**: The OAuth flow can't find a redirect URI.

**Solution**: Add all three URIs listed above.

### Still Not Working?

1. **Wait a few minutes** - Changes can take time to propagate
2. **Try again** - Run `./setup-oauth.sh` again
3. **Check the exact spelling** - URIs are case-sensitive
4. **Verify project** - Make sure you're editing the right project

## Why These URIs?

- **urn:ietf:wg:oauth:2.0:oob**: "Out of band" flow - Google shows you a code to copy/paste. Works everywhere (SSH, containers, etc.)

- **http://localhost**: Local HTTP server flow - More convenient when running on your desktop. Browser opens automatically.

- **http://127.0.0.1**: Same as localhost but using IP. Some systems prefer this.

## Alternative: Use Desktop App Type

When creating credentials, if you chose "Desktop app" as the application type, these redirect URIs should work automatically. If you chose "Web application", you might need to recreate as "Desktop app".

## Security Note

These redirect URIs are safe:
- `urn:ietf:wg:oauth:2.0:oob` - Standard OAuth 2.0 flow for installed apps
- `http://localhost` - Only accessible on your local machine
- No remote access possible

---

**Need more help?** Check the [Google OAuth documentation](https://developers.google.com/identity/protocols/oauth2/native-app).
