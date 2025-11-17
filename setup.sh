#!/bin/bash
# Gmail Fetcher - Setup Script
# This script helps you get started with Gmail Fetcher

set -e

echo "============================================"
echo "Gmail Fetcher - Interactive Setup"
echo "============================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    echo "Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker compose &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    echo "Please install Docker Compose first: https://docs.docker.com/compose/install/"
    exit 1
fi

echo -e "${GREEN}✓ Docker and Docker Compose are installed${NC}"
echo ""

# Create directories
echo "Creating required directories..."
mkdir -p secrets data
chmod 700 secrets data
echo -e "${GREEN}✓ Created secrets/ and data/ directories${NC}"

# Create placeholder archive password file (required for Docker secrets)
if [ ! -f secrets/archive_password.txt ]; then
    echo "changeme" > secrets/archive_password.txt
    chmod 600 secrets/archive_password.txt
    echo -e "${GREEN}✓ Created placeholder archive_password.txt${NC}"
fi
echo ""

# Create .env file
if [ -f .env ]; then
    echo -e "${YELLOW}⚠ .env file already exists${NC}"
    read -p "Overwrite it? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Keeping existing .env file"
    else
        cp .env.example .env
        echo -e "${GREEN}✓ Created new .env file${NC}"
    fi
else
    cp .env.example .env
    echo -e "${GREEN}✓ Created .env file from template${NC}"
fi
chmod 600 .env
echo ""

# Configure PUID/PGID
echo "File Ownership Configuration"
echo "-----------------------------"
echo "By default, files will be owned by UID 65532 (nonroot user)."
echo "You can set it to your user's ID for easier access (no sudo needed)."
echo ""
echo "Your current user: $(whoami) (UID: $(id -u), GID: $(id -g))"
echo ""
read -p "Use your user's UID/GID for file ownership? [Y/n] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    PUID=$(id -u)
    PGID=$(id -g)
    sed -i "s/PUID=.*/PUID=$PUID/" .env
    sed -i "s/PGID=.*/PGID=$PGID/" .env
    echo -e "${GREEN}✓ Set PUID=$PUID, PGID=$PGID${NC}"
    echo "  Files will be owned by $(whoami)"
else
    echo "Using default (UID 65532)"
    echo "  Note: You'll need sudo to access downloaded files"
fi
echo ""

# Check for credentials
if [ -f secrets/credentials.json ]; then
    echo -e "${GREEN}✓ Found existing credentials.json${NC}"
else
    echo -e "${YELLOW}⚠ No credentials.json found${NC}"
    echo ""
    echo "You need to obtain Gmail API credentials:"
    echo "1. Go to: https://console.cloud.google.com/"
    echo "2. Create a project and enable Gmail API"
    echo "3. Create OAuth2 credentials (Desktop app)"
    echo "4. Download the JSON file"
    echo ""
    read -p "Do you have the credentials file? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Enter path to credentials file: " creds_path
        if [ -f "$creds_path" ]; then
            cp "$creds_path" secrets/credentials.json
            chmod 600 secrets/credentials.json
            echo -e "${GREEN}✓ Copied credentials to secrets/credentials.json${NC}"
        else
            echo -e "${RED}✗ File not found: $creds_path${NC}"
            echo "Please copy manually to: secrets/credentials.json"
        fi
    else
        echo "Please copy your credentials file to: secrets/credentials.json"
    fi
fi
echo ""

# Archive password
echo "Archive Configuration (optional)"
echo "---------------------------------"
read -p "Do you want to enable encrypted archives? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -sp "Enter archive password: " password1
    echo
    read -sp "Confirm password: " password2
    echo
    if [ "$password1" = "$password2" ]; then
        echo "$password1" > secrets/archive_password.txt
        chmod 600 secrets/archive_password.txt

        # Update .env
        sed -i 's/ARCHIVE_ENABLED=false/ARCHIVE_ENABLED=true/' .env

        echo -e "${GREEN}✓ Archive password saved${NC}"
    else
        echo -e "${RED}✗ Passwords don't match${NC}"
    fi
fi
echo ""

# Gmail query configuration
echo "Gmail Query Configuration"
echo "-------------------------"
echo "What emails do you want to download?"
echo ""
echo "Examples:"
echo "  1. All emails (default)"
echo "  2. Emails with attachments"
echo "  3. From specific sender"
echo "  4. Date range"
echo "  5. Custom query"
echo ""
read -p "Choose [1-5]: " choice

case $choice in
    1)
        query="in:anywhere"
        ;;
    2)
        query="has:attachment"
        ;;
    3)
        read -p "Enter sender email: " sender
        query="from:$sender"
        ;;
    4)
        read -p "Start date (YYYY/MM/DD): " start_date
        read -p "End date (YYYY/MM/DD): " end_date
        query="after:$start_date before:$end_date"
        ;;
    5)
        read -p "Enter custom Gmail query: " query
        ;;
    *)
        query="in:anywhere"
        ;;
esac

# Update .env with query
sed -i "s|GMAIL_QUERY=.*|GMAIL_QUERY=$query|" .env
echo -e "${GREEN}✓ Gmail query configured: $query${NC}"
echo ""

# Max results
read -p "Limit number of emails to download? (0 for unlimited) [0]: " max_results
max_results=${max_results:-0}
sed -i "s|MAX_RESULTS=.*|MAX_RESULTS=$max_results|" .env
echo ""

# Summary
echo "============================================"
echo "Setup Summary"
echo "============================================"
echo ""
echo "Configuration:"
echo "  - Gmail Query: $query"
echo "  - Max Results: $max_results (0 = unlimited)"
echo "  - Archive: $(grep ARCHIVE_ENABLED .env | cut -d'=' -f2)"
echo ""
echo "Files:"
if [ -f secrets/credentials.json ]; then
    echo -e "  - Credentials: ${GREEN}✓ Present${NC}"
else
    echo -e "  - Credentials: ${RED}✗ Missing${NC}"
fi
echo "  - Configuration: .env"
echo "  - Data directory: ./data"
echo ""

# Build
echo "============================================"
echo "Next Steps"
echo "============================================"
echo ""
read -p "Build Docker image now? [Y/n] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    echo "Building Docker image..."
    docker compose build
    echo ""
    echo -e "${GREEN}✓ Build complete!${NC}"
    echo ""
fi

echo "Ready to run!"
echo ""
echo "Commands:"
echo "  make run        - Run with dashboard"
echo "  make run-batch  - Run without dashboard"
echo "  make help       - Show all commands"
echo ""
echo "Or manually:"
echo "  docker compose up"
echo ""
echo -e "${GREEN}Setup complete!${NC}"
