#!/bin/bash
# setup_symlinks.sh - Set up symlinks for portable Mini Agent deployment
# This script creates symlinks for system dependencies to make the deployment portable

set -e

echo "Mini Agent Symlink Setup"
echo "=========================="
echo ""

# Configuration
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYMLINKS_DIR="${REPO_DIR}/.system-symlinks"
mkdir -p "${SYMLINKS_DIR}"

echo "Repository directory: ${REPO_DIR}"
echo "Symlinks directory: ${SYMLINKS_DIR}"
echo ""

# Function to create symlink with error handling
create_symlink() {
    local target="$1"
    local link_name="$2"
    local description="$3"

    echo "Setting up: ${description}"

    if [[ ! -e "${target}" ]]; then
        echo "  ⚠️  WARNING: Target does not exist: ${target}"
        echo "     You may need to create this manually or install required software."
        return 1
    fi

    local link_path="${SYMLINKS_DIR}/${link_name}"

    # Remove existing symlink if it exists
    if [[ -L "${link_path}" ]]; then
        rm "${link_path}"
        echo "  ℹ️  Removed existing symlink"
    fi

    # Create new symlink (use relative path for portability)
    local target_rel_path="$(realpath --relative-to="${SYMLINKS_DIR}" "${target}" 2>/dev/null || echo "${target}")"
    ln -s "${target_rel_path}" "${link_path}"

    echo "  ✅ Created symlink: ${link_path} → ${target}"
    return 0
}

# Create symlinks for secrets
echo "Setting up secrets symlinks..."
echo "-------------------------------"

# Create local secrets directory
SECRETS_DIR="${REPO_DIR}/.secrets"
mkdir -p "${SECRETS_DIR}"

# If system secrets exist, symlink them
if [[ -f "/adapt/secrets/m2.env" ]]; then
    create_symlink "/adapt/secrets/m2.env" "m2.env" "API secrets file"
else
    echo "  ⚠️  No system secrets file found"
    echo "     Creating empty template..."
    touch "${SECRETS_DIR}/m2.env"
    echo '# MiniMax M2 API Key' > "${SECRETS_DIR}/m2.env"
    echo 'MiniMax_M2_CODE_PLAN_API_KEY="your-api-key-here"' >> "${SECRETS_DIR}/m2.env"
    echo "  ✅ Created template secrets file"
fi

echo ""
echo "Setting up configuration symlinks..."
echo "-------------------------------------"

# Systemd unit files (if they exist)
SYSTEMD_DIR="/etc/systemd/system"
if [[ -d "${SYSTEMD_DIR}" ]]; then
    echo "Found systemd directory: ${SYSTEMD_DIR}"
    echo "  (To create service files, run: ./install_systemd_service.sh)"
else
    echo "  ⚠️  Systemd not found (expected on non-systemd systems)"
fi

echo ""
echo "Creating portable configuration..."
echo "-----------------------------------"

# Create portable symlinks file
cat > "${REPO_DIR}/.symlinks-config.json" << EOF
{
  "symlinks_directory": "${SYMLINKS_DIR}",
  "secrets": {
    "source": "/adapt/secrets/m2.env",
    "link": "${SYMLINKS_DIR}/m2.env"
  },
  "created_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
}
EOF

echo "  ✅ Symlinks configuration saved to .symlinks-config.json"

echo ""
echo "Setting up environment activation script..."
echo "--------------------------------------------"

# Create environment activation script
cat > "${REPO_DIR}/activate-portable.sh" << 'EOF'
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
EOF

chmod +x "${REPO_DIR}/activate-portable.sh"
echo "  ✅ Created activate-portable.sh"

echo ""
echo "Setting up migration script..."
echo "-------------------------------"

# Create migration script
cat > "${REPO_DIR}/migrate-to-portable.sh" << 'EOF'
#!/bin/bash
# migrate-to-portable.sh - Migrate from system-based to portable deployment

set -e

echo "Migrate Mini Agent to Portable Mode"
echo "===================================="
echo ""

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="${REPO_DIR}/migration-backup-$(date +%Y%m%d-%H%M%S)"

# Create backup
mkdir -p "${BACKUP_DIR}"
echo "Creating backup in: ${BACKUP_DIR}"

echo "  Backing up configuration..."
cp -r "${REPO_DIR}"/*.yaml "${REPO_DIR}"/config* "${BACKUP_DIR}/" 2>/dev/null || true

echo "  Backing up secrets reference..."
if [[ -f "/adapt/secrets/m2.env" ]]; then
    cp "/adapt/secrets/m2.env" "${BACKUP_DIR}/m2.env.backup"
fi

echo ""
echo "Setting up portable symlinks..."
bash "${REPO_DIR}/setup_symlinks.sh"

echo ""
echo "Migration completed!"
echo "======================"
echo "Backup created at: ${BACKUP_DIR}"
echo ""
echo "Next steps:"
echo "1. Verify configuration: cat ${REPO_DIR}/.symlinks-config.json"
echo "2. Activate portable mode: source ${REPO_DIR}/activate-portable.sh"
echo "3. Test: mini-agent"
echo "4. Update systemd service to use portable paths if needed"
echo ""
echo "To revert, restore from backup:"
echo "  cp -r ${BACKUP_DIR}/* ${REPO_DIR}/"
echo "  rm -f ${REPO_DIR}/.system-symlinks/*"
EOF

chmod +x "${REPO_DIR}/migrate-to-portable.sh"
echo "  ✅ Created migrate-to-portable.sh"

echo ""
echo "Setup Complete!"
echo "==============="
echo ""
echo "Your Mini Agent is now configured for portable deployment."
echo ""
echo "Quick Start:"
echo "  1. source ${REPO_DIR}/activate-portable.sh"
echo "  2. mini-agent"
echo ""
echo "Migration:"
echo "  bash ${REPO_DIR}/migrate-to-portable.sh"
echo ""
echo "For systemd service installation:"
echo "  ./install_systemd_service.sh"
echo ""
echo "Documentation:"
echo "  - ${REPO_DIR}/PORTABLE_DEPLOYMENT.md"
echo "  - ${REPO_DIR}/MIGRATION_GUIDE.md"

# Check git status
echo ""
if [[ -d "${REPO_DIR}/.git" ]]; then
    echo "⚠️  Remember to commit these changes:"
    echo "   git add ."
    echo "   git commit -m 'Set up portable symlinks and deployment files'"
fi
