# Deployment Modes: Security vs Convenience

Gmail Fetcher offers two deployment modes with different security/convenience trade-offs.

## Quick Comparison

| Feature | Flexible Mode | Distroless Mode |
|---------|--------------|-----------------|
| **Base Image** | `python:3.11-slim` | `gcr.io/distroless/python3` |
| **PUID/PGID Support** | ✅ Yes | ❌ No |
| **File Ownership** | Your choice (1000:1000, etc.) | Fixed (65532:65532) |
| **Shell Access** | ⚠️ Has /bin/bash | ✅ No shell |
| **Package Manager** | ⚠️ Has apt | ✅ None |
| **Image Size** | ~150MB | ~50MB |
| **Read-Only FS** | ❌ No (needs to chown) | ✅ Yes |
| **Attack Surface** | Medium | Minimal |
| **Ease of Use** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Security** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

## Flexible Mode (Default)

**Best for**: Most users who want convenience and standard UID/GID

### Features
- ✅ Set `PUID` and `PGID` to match your user (e.g., 1000:1000)
- ✅ Files created with your ownership - no sudo needed
- ✅ Easy file access and manipulation
- ✅ Still runs as non-root user
- ✅ Still drops all capabilities
- ✅ Still uses Docker secrets

### Usage

```bash
# Use your user's UID/GID (typical: 1000:1000)
echo "PUID=1000" >> .env
echo "PGID=1000" >> .env

# Run normally
docker-compose up
```

Or set at runtime:
```bash
PUID=1000 PGID=1000 docker-compose up
```

### Security Considerations
- Has shell (`/bin/bash`) - potential escape vector
- Has package manager (`apt`) - could install packages if compromised
- Writable filesystem at /data (needed for chown)
- Slightly larger attack surface

**Still secure**: Runs as non-root, drops capabilities, uses secrets, no new privileges

## Distroless Mode (Maximum Security)

**Best for**: Security-focused deployments, production, compliance requirements

### Features
- ✅ No shell - impossible to execute arbitrary commands
- ✅ No package manager - can't install malware
- ✅ Read-only filesystem - can't modify binaries
- ✅ Minimal dependencies - smallest attack surface
- ✅ Smaller image size - faster downloads

### Usage

```bash
# Use distroless compose file
docker-compose -f docker-compose.distroless.yml up
```

Or with Makefile:
```bash
make run-distroless
```

### File Ownership
Files will be owned by UID 65532 (nonroot). To access:

```bash
# Option 1: Use sudo
sudo ls -la data/

# Option 2: Change ownership after download
sudo chown -R $(id -u):$(id -g) data/

# Option 3: Add yourself to GID 65532
sudo usermod -a -G 65532 $USER
newgrp 65532
```

### Security Considerations
- ✅ Maximum security - Google's recommended practice
- ✅ No attack vectors through shell or package manager
- ✅ Used by major companies for production workloads
- ⚠️ Files owned by UID 65532 (requires sudo or chown)

## Which Should I Use?

### Choose Flexible Mode if:
- ✅ You want files owned by your user (1000:1000)
- ✅ You don't want to use sudo to access downloads
- ✅ Convenience is important
- ✅ Running on personal machine
- ✅ You trust your network/environment

### Choose Distroless Mode if:
- ✅ Maximum security is priority
- ✅ Running in production environment
- ✅ Compliance requirements
- ✅ Public-facing server
- ✅ You don't mind using sudo or chown
- ✅ You want Google's recommended security practices

## Switching Between Modes

### From Flexible to Distroless

```bash
# Files are already created by your user, need to change ownership
sudo chown -R 65532:65532 data/

# Run with distroless
docker-compose -f docker-compose.distroless.yml up
```

### From Distroless to Flexible

```bash
# Files owned by 65532, take ownership
sudo chown -R $(id -u):$(id -g) data/

# Or set PUID/PGID and let entrypoint handle it
PUID=$(id -u) PGID=$(id -g) docker-compose up
```

## Technical Details

### Flexible Mode Architecture

```
┌─────────────────────────────────────┐
│ Container Start                      │
├─────────────────────────────────────┤
│ 1. Entrypoint runs as root           │
│ 2. Creates user with PUID/PGID       │
│ 3. chown /data to PUID:PGID          │
│ 4. exec gosu PUID:PGID python ...    │
│    (drops to non-root)               │
└─────────────────────────────────────┘
```

**Key**: Uses `gosu` to safely drop privileges after setup

### Distroless Mode Architecture

```
┌─────────────────────────────────────┐
│ Container Start                      │
├─────────────────────────────────────┤
│ 1. Starts directly as UID 65532      │
│ 2. No privilege escalation possible  │
│ 3. Read-only filesystem              │
│ 4. No shell or utilities available   │
└─────────────────────────────────────┘
```

**Key**: Never runs as root, even momentarily

## Real-World Example

### Personal Laptop (Flexible)
```bash
# ~/.config/gmail-fetcher/.env
PUID=1000
PGID=1000
GMAIL_QUERY=in:anywhere

# Easy access
ls -la ~/gmail-backups/data/
# drwxr-xr-x  user  user  ...
```

### Production Server (Distroless)
```bash
# /srv/gmail-fetcher/.env
GMAIL_QUERY=from:critical@company.com

# Secure deployment
docker-compose -f docker-compose.distroless.yml up

# Access with service account
sudo -u backup ls /srv/gmail-fetcher/data/
# Or add backup user to GID 65532
```

## Makefile Shortcuts

I'll add these to the Makefile:

```bash
make run              # Flexible mode (default)
make run-distroless   # Distroless mode
make build-both       # Build both images
```

## Recommendation

**For your use case (1000:1000)**: Use **Flexible Mode**

You mentioned wanting to avoid sudo for day-to-day access, which is exactly what flexible mode provides. You still get:
- Non-root execution
- No new privileges
- Capability dropping
- Docker secrets
- Network isolation

The security difference is real but modest for a **local, personal** deployment. If you were running this on a public server or handling highly sensitive data, distroless would be better.

## Security Checklist (Both Modes)

- [ ] Credentials stored as Docker secrets
- [ ] Container runs as non-root (both modes)
- [ ] All capabilities dropped (both modes)
- [ ] No new privileges allowed (both modes)
- [ ] Resource limits set (both modes)
- [ ] Regular security updates
- [ ] Strong archive passwords
- [ ] OAuth tokens protected

Both modes are **significantly more secure** than most Docker containers. Choose based on your convenience needs.

---

**Bottom line**: Flexible mode is still very secure and gives you the file ownership you want. Distroless is maximum paranoia mode.
