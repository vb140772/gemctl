#!/bin/bash
#
# Installation script for gemctl wrapper
# This script installs the gemctl wrapper to provide gemctl-style commands for Agentspace
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Installing gemctl wrapper for Agentspace CLI...${NC}"

# Check if we're in the right directory
if [ ! -f "gemctl.sh" ]; then
    echo -e "${RED}Error: gemctl.sh not found. Please run this script from the gemctl directory.${NC}"
    exit 1
fi

# Check if gemctl CLI is available
if ! command -v gemctl >/dev/null 2>&1 && ! python3 -c "import gemctl" 2>/dev/null; then
    echo -e "${YELLOW}Warning: gemctl CLI not found. Please install it first:${NC}"
    echo "  pip install -e ."
    echo "  or"
    echo "  python3 -m pip install -r requirements.txt"
    echo ""
fi

# Create backup of existing gemctl if it exists
if [ -f "/opt/homebrew/bin/gemctl" ]; then
    echo -e "${YELLOW}Backing up existing gemctl to gemctl-real...${NC}"
    sudo mv /opt/homebrew/bin/gemctl /opt/homebrew/bin/gemctl-real
fi

# Install the wrapper
echo -e "${GREEN}Installing gemctl wrapper...${NC}"
sudo cp gemctl.sh /opt/homebrew/bin/gemctl
sudo chmod +x /opt/homebrew/bin/gemctl

echo -e "${GREEN}✅ gemctl wrapper installed successfully!${NC}"
echo ""
echo "You can now use gemctl commands:"
echo "  gemctl engines list"
echo "  gemctl engines describe ENGINE_ID"
echo "  gemctl data-stores list"
echo ""
echo "For the original gemctl CLI, use:"
echo "  /opt/homebrew/bin/gemctl-real"
echo ""
echo "To uninstall, run:"
echo "  sudo rm /opt/homebrew/bin/gemctl"
echo "  sudo mv /opt/homebrew/bin/gemctl-real /opt/homebrew/bin/gemctl"
