# Security Policy

## Security Philosophy

Gmail Fetcher is designed with security and transparency as first-class priorities. This document outlines our security practices and how to report vulnerabilities.

## Security Features

### Container Security

1. **Distroless Base Image**
   - Uses `gcr.io/distroless/python3-debian12:nonroot`
   - No shell, package managers, or unnecessary binaries
   - Minimal attack surface

2. **Non-Root Execution**
   - Container runs as user `nonroot` (UID 65532)
   - Never executes with root privileges
   - Prevents privilege escalation attacks

3. **Read-Only Filesystem**
   - Container filesystem is read-only by default
   - Only `/data` and `/tmp` are writable
   - Prevents unauthorized file modifications

4. **Capability Dropping**
   - All Linux capabilities are dropped
   - Principle of least privilege
   - Reduces kernel attack surface

5. **Security Options**
   - `no-new-privileges` prevents privilege escalation
   - Resource limits prevent DoS
   - Network isolation available

### Credential Management

1. **Docker Secrets**
   - Credentials stored as Docker secrets, not environment variables
   - Secrets mounted read-only at `/run/secrets/`
   - Never logged or exposed in docker inspect

2. **OAuth2 Flow**
   - Uses official Google OAuth2
   - No password storage
   - Token refresh handled automatically

3. **File Permissions**
   - Credentials: `600` (owner read/write only)
   - Secrets directory: `700` (owner access only)
   - Validated by `make security-check`

### Data Protection

1. **Local Only**
   - No cloud uploads
   - All data stays on your machine
   - No telemetry or analytics

2. **Encrypted Archives**
   - Optional AES-256 encrypted 7z archives
   - Password-protected
   - Secure deletion of temporary files

3. **Git Protection**
   - `.gitignore` prevents committing secrets
   - Sensitive files explicitly excluded
   - Security check validates this

## Security Best Practices

### For Users

1. **Credential Protection**
   ```bash
   # Set proper permissions
   chmod 600 secrets/credentials.json
   chmod 600 .env
   chmod 700 secrets

   # Run security check
   make security-check
   ```

2. **Regular Audits**
   - Review OAuth2 permissions regularly
   - Check Google account access: https://myaccount.google.com/permissions
   - Rotate credentials periodically

3. **Token Management**
   - Store `token.json` securely
   - Don't share or commit to version control
   - Revoke if compromised

4. **Archive Passwords**
   - Use strong, unique passwords
   - Store in password manager
   - Don't lose them (AES-256 can't be recovered)

5. **Host Security**
   - Keep Docker updated
   - Secure your Docker host
   - Use firewall rules
   - Monitor Docker daemon

6. **Limited Scope**
   - Use specific Gmail queries
   - Don't download more than needed
   - Test with small datasets first

### For Developers

1. **Code Review**
   - All code changes require review
   - Security-sensitive changes need extra scrutiny
   - Check for injection vulnerabilities

2. **Dependency Management**
   - Keep dependencies updated
   - Use `pip-audit` or similar tools
   - Pin versions in requirements.txt

3. **Testing**
   - Test with sanitized data
   - Never commit test credentials
   - Use separate test accounts

4. **Logging**
   - Never log credentials or tokens
   - Sanitize email content in logs
   - Use appropriate log levels

## Threat Model

### In Scope

- Container escape
- Credential exposure
- Code injection
- Privilege escalation
- Data exfiltration
- Token theft

### Out of Scope

- Gmail account compromise (use 2FA)
- Host OS vulnerabilities
- Physical access to host
- Social engineering
- Denial of service against Gmail

## Known Limitations

1. **OAuth Flow**
   - First-time setup requires browser access
   - Local HTTP server for callback
   - Not suitable for headless servers without manual token transfer

2. **Token Storage**
   - Token stored as JSON file
   - Protected by filesystem permissions only
   - Consider encrypted storage for high-security needs

3. **Archive Security**
   - 7z encryption relies on py7zr library
   - Password strength is user-dependent
   - No built-in key derivation hardening

## Reporting Vulnerabilities

### How to Report

If you discover a security vulnerability, please:

1. **Do NOT** open a public GitHub issue
2. Email details to: [your-security-email@example.com]
3. Include:
   - Description of vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### Response Timeline

- **24 hours**: Initial acknowledgment
- **7 days**: Assessment and planned response
- **30 days**: Fix released (or timeline communicated)

### Disclosure Policy

- We practice responsible disclosure
- We'll credit reporters (unless anonymity requested)
- We'll coordinate public disclosure timing
- We'll issue security advisories for confirmed issues

## Security Checklist

Before deploying to production:

- [ ] Credentials stored as Docker secrets
- [ ] File permissions set correctly (`make security-check`)
- [ ] `.env` not committed to git
- [ ] Archive passwords strong and stored securely
- [ ] Tested with limited dataset first
- [ ] DELETE_AFTER_DOWNLOAD disabled (unless intended)
- [ ] Container running as non-root
- [ ] Host system patched and updated
- [ ] Docker daemon secured
- [ ] Logs reviewed for sensitive data
- [ ] OAuth2 permissions reviewed
- [ ] Backup strategy in place

## Security Updates

Check for updates regularly:

```bash
git pull
docker-compose build --no-cache
```

Subscribe to repository releases for security announcements.

## Compliance

This tool:
- Uses official Google APIs
- Follows OAuth2 best practices
- Respects Gmail Terms of Service
- Stores data locally (GDPR-friendly)
- Provides data portability

## Contact

For security concerns: [your-security-email@example.com]
For general issues: GitHub Issues

## Acknowledgments

Security best practices inspired by:
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CIS Docker Benchmarks](https://www.cisecurity.org/benchmark/docker)
- [Google Distroless](https://github.com/GoogleContainerTools/distroless)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)

---

**Last Updated**: 2024-11-17
**Version**: 1.0.0
