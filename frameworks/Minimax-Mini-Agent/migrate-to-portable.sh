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
