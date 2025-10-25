#!/bin/bash
#
# Uninstallation script for gemctl wrapper
# This script removes the gemctl wrapper and restores the original gemctl CLI
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Uninstalling gemctl wrapper for Agentspace CLI...${NC}"

# Check if wrapper is installed
if [ ! -f "/opt/homebrew/bin/gemctl" ]; then
    echo -e "${RED}Error: gemctl wrapper not found at /opt/homebrew/bin/gemctl${NC}"
    exit 1
fi

# Remove the wrapper
echo -e "${YELLOW}Removing gemctl wrapper...${NC}"
sudo rm /opt/homebrew/bin/gemctl

# Restore original gemctl if it exists
if [ -f "/opt/homebrew/bin/gemctl-real" ]; then
    echo -e "${GREEN}Restoring original gemctl CLI...${NC}"
    sudo mv /opt/homebrew/bin/gemctl-real /opt/homebrew/bin/gemctl
    echo -e "${GREEN}✅ Original gemctl CLI restored!${NC}"
else
    echo -e "${YELLOW}No original gemctl CLI found to restore.${NC}"
fi

echo -e "${GREEN}✅ gemctl wrapper uninstalled successfully!${NC}"
echo ""
echo "You can still use gemctl directly:"
echo "  python -m gemctl engines list"
echo "  pip install -e . && gemctl engines list"
