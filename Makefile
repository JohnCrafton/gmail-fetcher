.PHONY: help setup build build-distroless build-both run run-distroless run-batch dash clean test security-check

# Default target
help:
	@echo "Gmail Fetcher - Make targets"
	@echo ""
	@echo "Setup:"
	@echo "  make setup          - Initial setup (create dirs, copy .env.example)"
	@echo "  make build          - Build flexible Docker image (with PUID/PGID)"
	@echo "  make build-distroless - Build distroless image (max security)"
	@echo "  make build-both     - Build both images"
	@echo ""
	@echo "Run:"
	@echo "  make run            - Run with dashboard (flexible mode, PUID/PGID)"
	@echo "  make run-distroless - Run with distroless mode (max security)"
	@echo "  make run-batch      - Run without dashboard (batch mode)"
	@echo "  make dash           - Alias for 'make run'"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean          - Clean downloaded data (keeps credentials)"
	@echo "  make clean-all      - Clean everything including tokens"
	@echo "  make security-check - Run security validation checks"
	@echo "  make logs           - View container logs"
	@echo ""
	@echo "Development:"
	@echo "  make dev-install    - Install dependencies with uv (fast!)"
	@echo "  make dev-install-editable - Install in editable mode with uv"
	@echo "  make dev-run        - Run locally without Docker"
	@echo ""

# Initial setup
setup:
	@echo "Setting up Gmail Fetcher..."
	@mkdir -p secrets data
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "Created .env file - please edit with your settings"; \
	fi
	@if [ ! -f secrets/archive_password.txt ]; then \
		echo "changeme" > secrets/archive_password.txt; \
		chmod 600 secrets/archive_password.txt; \
		echo "Created placeholder secrets/archive_password.txt"; \
	fi
	@chmod 700 secrets data
	@echo ""
	@echo "Setup complete! Next steps:"
	@echo "1. Copy your Gmail API credentials to: secrets/credentials.json"
	@echo "2. Edit .env with your configuration"
	@echo "3. (Optional) Set archive password: echo 'your-password' > secrets/archive_password.txt"
	@echo "4. Run 'make build' to build the Docker image"
	@echo "5. Run 'make run' to start with dashboard"

# Build flexible Docker image (with PUID/PGID support)
build:
	@echo "Building flexible Docker image (with PUID/PGID support)..."
	docker compose build
	@echo "Build complete!"

# Build distroless Docker image (maximum security)
build-distroless:
	@echo "Building distroless Docker image (maximum security)..."
	docker compose -f docker compose.distroless.yml build
	@echo "Build complete!"

# Build both images
build-both: build build-distroless
	@echo "Both images built successfully!"

# Run with dashboard (flexible mode)
run: build
	@echo "Starting Gmail Fetcher with dashboard (flexible mode)..."
	@echo "Using PUID=$${PUID:-65532} PGID=$${PGID:-65532}"
	docker compose up

# Run with dashboard (distroless mode - maximum security)
run-distroless: build-distroless
	@echo "Starting Gmail Fetcher with dashboard (distroless mode)..."
	@echo "⚠️  Files will be owned by UID 65532"
	docker compose -f docker compose.distroless.yml up

# Run without dashboard (batch mode)
run-batch: build
	@echo "Starting Gmail Fetcher in batch mode..."
	docker compose run --rm gmail-fetcher

# Alias for run
dash: run

# View logs
logs:
	docker compose logs -f

# Clean downloaded emails but keep credentials and tokens
clean:
	@echo "Cleaning downloaded emails..."
	@read -p "This will delete all downloaded emails in data/emails/. Continue? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		rm -rf data/emails; \
		echo "Cleaned!"; \
	else \
		echo "Cancelled."; \
	fi

# Clean everything including tokens (will require re-authentication)
clean-all:
	@echo "⚠️  WARNING: This will delete ALL data including OAuth tokens!"
	@echo "You will need to re-authenticate on next run."
	@read -p "Delete everything in data/? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		rm -rf data/*; \
		echo "Cleaned!"; \
	else \
		echo "Cancelled."; \
	fi

# Security validation checks
security-check:
	@echo "Running security checks..."
	@echo ""
	@echo "1. Checking for accidentally committed secrets..."
	@if git ls-files | grep -qE 'credentials\.json|token\.json|archive_password\.txt'; then \
		echo "  ❌ FAIL: Found sensitive files in git!"; \
		git ls-files | grep -E 'credentials\.json|token\.json|archive_password\.txt'; \
		exit 1; \
	else \
		echo "  ✅ PASS: No sensitive files in git"; \
	fi
	@echo ""
	@echo "2. Checking secrets directory permissions..."
	@if [ -d secrets ]; then \
		perms=$$(stat -c '%a' secrets); \
		if [ "$$perms" = "700" ]; then \
			echo "  ✅ PASS: secrets/ has correct permissions (700)"; \
		else \
			echo "  ⚠️  WARNING: secrets/ has permissions $$perms, should be 700"; \
		fi; \
	fi
	@echo ""
	@echo "3. Checking credentials.json permissions..."
	@if [ -f secrets/credentials.json ]; then \
		perms=$$(stat -c '%a' secrets/credentials.json); \
		if [ "$$perms" = "600" ]; then \
			echo "  ✅ PASS: credentials.json has correct permissions (600)"; \
		else \
			echo "  ⚠️  WARNING: credentials.json has permissions $$perms, should be 600"; \
		fi; \
	else \
		echo "  ⚠️  WARNING: credentials.json not found"; \
	fi
	@echo ""
	@echo "4. Checking .env file permissions..."
	@if [ -f .env ]; then \
		perms=$$(stat -c '%a' .env); \
		if [ "$$perms" = "600" ]; then \
			echo "  ✅ PASS: .env has correct permissions (600)"; \
		else \
			echo "  ⚠️  WARNING: .env has permissions $$perms, should be 600"; \
			echo "  Run: chmod 600 .env"; \
		fi; \
	fi
	@echo ""
	@echo "5. Checking for .env in git..."
	@if git ls-files | grep -q '^\.env$$'; then \
		echo "  ❌ FAIL: .env is tracked by git!"; \
		exit 1; \
	else \
		echo "  ✅ PASS: .env is not tracked by git"; \
	fi
	@echo ""
	@echo "Security check complete!"

# Development: Install dependencies locally with uv
dev-install:
	@echo "Installing dependencies for local development with uv..."
	@if ! command -v uv &> /dev/null; then \
		echo "Installing uv..."; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
	fi
	uv venv
	uv pip install -r requirements.txt
	@echo "Done! Activate with: source .venv/bin/activate"

# Development: Install in editable mode
dev-install-editable:
	@echo "Installing in editable mode with uv..."
	@if ! command -v uv &> /dev/null; then \
		echo "Installing uv..."; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
	fi
	uv venv
	uv pip install -e .
	@echo "Done! Activate with: source .venv/bin/activate"

# Development: Run locally
dev-run:
	@if [ ! -d .venv ]; then \
		echo "Virtual environment not found. Run 'make dev-install' first."; \
		exit 1; \
	fi
	@echo "Running locally..."
	. .venv/bin/activate && python gmail-fetcher.py --dash
