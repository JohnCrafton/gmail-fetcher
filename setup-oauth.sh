#!/bin/bash
# Gmail Fetcher - OAuth Setup Helper
# This script helps you set up OAuth authentication easily

set -e

echo "============================================"
echo "📧 Gmail Fetcher - OAuth Setup"
echo "============================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check for credentials file
if [ ! -f secrets/credentials.json ]; then
    echo -e "${RED}Error: secrets/credentials.json not found${NC}"
    echo ""
    echo "You need to get Gmail API credentials first:"
    echo "1. Go to https://console.cloud.google.com/"
    echo "2. Create a project and enable Gmail API"
    echo "3. Create OAuth2 credentials (Desktop app)"
    echo "4. Download the JSON file"
    echo "5. Save it as secrets/credentials.json"
    echo ""
    exit 1
fi

echo -e "${GREEN}✓ Found credentials.json${NC}"
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Installing uv (fast Python package manager)..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# Remove broken venv if it exists
if [ -d .venv ] && [ ! -f .venv/bin/python3 ]; then
    echo "Removing broken virtual environment..."
    rm -rf .venv
fi

# Create virtual environment if needed
if [ ! -d .venv ]; then
    echo "Creating virtual environment..."
    uv venv
fi

# Install dependencies
echo "Installing dependencies with uv..."
uv pip install -r requirements.txt

# Activate venv
source .venv/bin/activate

# Create local data directory
mkdir -p data
chmod 700 data

# Copy credentials to current directory for local run
cp secrets/credentials.json credentials.json 2>/dev/null || true

echo ""
echo "============================================"
echo "OAuth Credentials Type Check"
echo "============================================"
echo ""
echo "Make sure you have:"
echo ""
echo -e "${GREEN}✓ OAuth 2.0 Client ID (Desktop app type)${NC}"
echo "  Saved as: secrets/credentials.json"
echo ""
echo "Desktop app credentials work automatically with localhost."
echo "No redirect URI configuration needed!"
echo ""
read -p "Do you have Desktop app credentials? [Y/n] " -n 1 -r
echo
if [[ $REPLY =~ ^[Nn]$ ]]; then
    echo ""
    echo -e "${YELLOW}Please create Desktop app credentials:${NC}"
    echo "  1. Go to https://console.cloud.google.com/"
    echo "  2. APIs & Services → Credentials"
    echo "  3. Create Credentials → OAuth client ID"
    echo "  4. Choose 'Desktop app'"
    echo "  5. Download JSON and save as secrets/credentials.json"
    echo ""
    exit 1
fi

echo ""
echo "============================================"
echo "Starting OAuth Flow"
echo "============================================"
echo ""
echo "The script will:"
echo "  1. Show you a Google authorization URL"
echo "  2. You'll authorize the app in your browser"
echo "  3. You'll paste the authorization code back here"
echo "  4. Token will be saved to data/token.json"
echo ""
read -p "Press Enter to continue..."
echo ""

# Run the OAuth flow - WITHOUT --no-auth-browser for local run
# This will use run_local_server which works with Desktop app credentials
python gmail-fetcher.py --verbose

# Check if token was created
if [ -f data/token.json ]; then
    echo ""
    echo "============================================"
    echo -e "${GREEN}✓ OAuth Setup Complete!${NC}"
    echo "============================================"
    echo ""
    echo "Token saved to: data/token.json"
    echo ""
    echo "For Docker deployment, copy the token:"
    echo -e "${YELLOW}  cp data/token.json /media/12TB/backup/gmail_data/${NC}"
    echo ""
    echo "Or update docker-compose.yml to mount ./data:/data"
    echo ""
    echo "Now you can run:"
    echo "  - Locally: python gmail-fetcher.py --dash"
    echo "  - Docker:  docker compose up"
    echo ""
else
    echo ""
    echo -e "${RED}✗ OAuth setup failed${NC}"
    echo "Token file not created. Please try again."
    echo ""
    exit 1
fi
