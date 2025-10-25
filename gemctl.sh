#!/bin/bash
#
# gemctl wrapper for Agentspace CLI
# Provides gemctl-style commands for Google Cloud Agentspace (Discovery Engine) resources
#
# Usage: gemctl <command> [options]
# Example: gemctl engines list --project-id=my-project
#

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Find the gemctl CLI
GEMCTL_CLI=""
if command -v gemctl >/dev/null 2>&1; then
    GEMCTL_CLI="gemctl"
elif command -v python3 >/dev/null 2>&1; then
    # Try to find gemctl module
    if python3 -c "import gemctl" 2>/dev/null; then
        GEMCTL_CLI="python3 -m gemctl"
    fi
fi

# If gemctl not found, show error
if [ -z "$GEMCTL_CLI" ]; then
    echo "Error: gemctl CLI not found. Please install it first:" >&2
    echo "  pip install -e ." >&2
    echo "  or" >&2
    echo "  python3 -m pip install -r requirements.txt" >&2
    echo "" >&2
    echo "After installation, you can use:" >&2
    echo "  gemctl engines list" >&2
    echo "  python -m gemctl engines list" >&2
    exit 1
fi

# Execute the gemctl command with all arguments
if [[ "$GEMCTL_CLI" == *"python3 -m gemctl"* ]]; then
    python3 -m gemctl "$@"
else
    $GEMCTL_CLI "$@"
fi
