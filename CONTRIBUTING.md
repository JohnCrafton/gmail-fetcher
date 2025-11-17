# Contributing to Gmail Fetcher

Thank you for considering contributing to Gmail Fetcher!

## Development Setup

We use **uv** for Python package management - it's much faster than pip.

### Quick Start

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repo
git clone <repo-url>
cd gmail-fetcher

# Create venv and install dependencies
uv venv
uv pip install -r requirements.txt

# Or install in editable mode (recommended for development)
uv pip install -e ".[dev]"

# Activate environment
source .venv/bin/activate
```

### Development Workflow

```bash
# Make your changes
vim src/some_file.py

# Run locally to test
python gmail-fetcher.py --dash

# Format and lint (if you installed dev dependencies)
ruff check .
ruff format .

# Build Docker image to test
docker compose build

# Test the container
docker compose up
```

## Project Structure

```
gmail-fetcher/
├── src/                  # Application code
│   ├── main.py          # Entry point
│   ├── config.py        # Configuration
│   ├── gmail_client.py  # Gmail API client with rate limiting
│   ├── downloader.py    # Email download logic
│   ├── archiver.py      # Archive creation
│   └── dashboard.py     # Terminal UI
├── Dockerfile           # Flexible mode (PUID/PGID)
├── Dockerfile.distroless # Maximum security mode
├── pyproject.toml       # Python project metadata
└── requirements.txt     # Dependencies
```

## Code Style

We use **ruff** for linting and formatting:

```bash
# Install dev dependencies
uv pip install -e ".[dev]"

# Check code
ruff check .

# Format code
ruff format .
```

## Testing

```bash
# Test with limited emails
MAX_RESULTS=10 python gmail-fetcher.py

# Test with dashboard
python gmail-fetcher.py --dash

# Test Docker build
docker compose build
docker compose up
```

## Pull Request Process

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test locally and in Docker
5. Run ruff to format/lint
6. Commit with clear messages
7. Push and create a PR

## Commit Messages

Use clear, descriptive commit messages:

```
Add rate limiting to attachment downloads

- Apply exponential backoff to attachment API calls
- Track rate limit hits in statistics
- Update dashboard to show retry counts
```

## Adding Dependencies

```bash
# Add to requirements.txt
echo "new-package>=1.0.0" >> requirements.txt

# Or add to pyproject.toml [project.dependencies]
# Then sync:
uv pip install -r requirements.txt
```

## Security

- Never commit credentials or tokens
- Run `make security-check` before committing
- Review `.gitignore` if adding new file types
- Test with minimal permissions

## Questions?

Open an issue or start a discussion!

---

**Happy coding!** 🚀
