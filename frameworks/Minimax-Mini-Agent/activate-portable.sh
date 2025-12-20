#!/bin/bash
# activate-portable.sh - Activate Mini Agent in portable mode

MINI_AGENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Set environment variables for portable mode
export MINI_AGENT_PORTABLE_MODE=1
export MINI_AGENT_REPO_DIR="${MINI_AGENT_DIR}"

# Add to PATH if not already there
if [[ ":$PATH:" != *":${MINI_AGENT_DIR}/.system-symlinks:"* ]]; then
    export PATH="${MINI_AGENT_DIR}/.system-symlinks:${PATH}"
fi

echo "Mini Agent portable mode activated"
echo "Repository: ${MINI_AGENT_DIR}"
echo "Run 'mini-agent' to start"
