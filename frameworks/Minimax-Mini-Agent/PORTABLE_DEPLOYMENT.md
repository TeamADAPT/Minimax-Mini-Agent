# Portable Mini Agent Deployment Guide

## Overview

This guide explains how to deploy Mini Agent as a fully self-contained, portable system. Everything is stored in the repository directory, making it easy to move, backup, or deploy to new systems.

## Architecture

### Self-Contained Directory Structure

```
/adapt/platform/novaops/frameworks/Minimax-Mini-Agent/
├── mini_agent/                          # Main package
│   ├── config/
│   │   ├── config.yaml                 # Configuration
│   │   ├── config-example.yaml         # Example config
│   │   ├── mcp.json                    # MCP configuration
│   │   └── TeamADAPT_Rules.md          # Rules & protocols
│   ├── __init__.py
│   ├── agent.py
│   ├── cli.py                          # Enhanced CLI
│   ├── config.py                       # Config loading
│   ├── a2a_comms.py                    # A2A communication
│   ├── rules_loader.py                 # Rules hotloading
│   └── session_manager.py              # Session management
├── .agent-sessions/                     # Auto-saved sessions
│   └── <workspace-sessions>
├── .system-symlinks/                    # Symlinks to system resources
│   └── m2.env → /adapt/secrets/m2.env   # API secrets
├── .secrets/                            # Local secrets (fallback)
│   └── m2.env
├── .symlinks-config.json               # Symlink configuration
├── activate-portable.sh                # Environment activation
├── migrate-to-portable.sh              # Migration script
├── setup_symlinks.sh                   # Symlink setup
├── self_modification_workflow.py       # Self-modification demo
├── pyproject.toml                      # Package configuration
├── uv.lock                            # Dependency lock
└── README.md
```

## Key Principles

### 1. **Everything in One Place**
- All configuration in the repository
- Sessions stored in workspace subdirectories
- Rules copied to repo config directory
- Portable activation script

### 2. **System Resources via Symlinks**
- Don't copy sensitive files (maintain security)
- Use symlinks to reference system resources
- Fallback to local copies if symlinks unavailable
- Document all external dependencies

### 3. **Easy Migration**
- One command to migrate from system to portable
- Backup before making changes
- Revert capability built-in
- Clear documentation of all changes

### 4. **No Breaking Changes**
- System-based deployment still works
- Portable mode is opt-in
- Backward compatible
- Gradual migration path

## Quick Start (Portable Mode)

**To use fully portable mode:**

1. **Set up symlinks** (run once):
   ```bash
   ./setup_symlinks.sh
   ```

2. **Activate portable environment**:
   ```bash
   source activate-portable.sh
   ```

3. **Run Mini Agent**:
   ```bash
   mini-agent
   ```
   *Automatically uses local configuration and symlinks*

## Detailed Setup Process

### Step 1: Initial Setup

```bash
cd /adapt/platform/novaops/frameworks/Minimax-Mini-Agent

# Set up symlinks for system resources
./setup_symlinks.sh

# Output:
# ✅ Created symlink: /adapt/platform/novaops/frameworks/Minimax-Mini-Agent/.system-symlinks/m2.env → /adapt/secrets/m2.env
# ✅ Created activate-portable.sh
# ✅ Created migrate-to-portable.sh
```

### Step 2: Verify Symlinks

```bash
cd /adapt/platform/novaops/frameworks/Minimax-Mini-Agent

# Check symlinks
ls -la .system-symlinks/

# Expected output:
# lrwxrwxrwx 1 user user  21 Dec 16 18:00 m2.env -> /adapt/secrets/m2.env

# Check configuration
cat .symlinks-config.json
```

### Step 3: Activate Portable Mode

```bash
# Source the activation script
source activate-portable.sh

# Output:
# Mini Agent portable mode activated
# Repository: /adapt/platform/novaops/frameworks/Minimax-Mini-Agent
# Run 'mini-agent' to start

# Now run Mini Agent (uses portable config)
mini-agent
```

## Symlink Management

### Creating Custom Symlinks

```bash
#!/bin/bash
# custom-symlink.sh - Create additional symlinks

cd /adapt/platform/novaops/frameworks/Minimax-Mini-Agent

# Create symlink for custom data directory
ln -s /data/shared/agent-data .system-symlinks/shared-data

# Create symlink for logs
ln -s /var/log/mini-agent .system-symlinks/logs
```

### Removing Symlinks

```bash
cd /adapt/platform/novaops/frameworks/Minimax-Mini-Agent

# Remove a specific symlink
rm .system-symlinks/m2.env

# Remove all symlinks
rm -rf .system-symlinks/*
```

### Updating Symlinks

```bash
cd /adapt/platform/novaops/frameworks/Minimax-Mini-Agent

# Remove old symlink
rm .system-symlinks/m2.env

# Create new one pointing to different location
ln -s /new/path/to/secrets/m2.env .system-symlinks/m2.env
```

## Migration from System to Portable

### Automatic Migration

```bash
cd /adapt/platform/novaops/frameworks/Minimax-Mini-Agent

# Run migration script
./migrate-to-portable.sh

# What it does:
# 1. Creates backup of current state
# 2. Copies rules file to repo
# 3. Sets up symlinks
# 4. Creates activation script
# 5. Provides revert instructions
```

### Manual Migration Steps

For full control, migrate manually:

```bash
cd /adapt/platform/novaops/frameworks/Minimax-Mini-Agent

# 1. Backup current config
BACKUP_DIR="backup-$(date +%Y%m%d-%H%M%S)"
mkdir "${BACKUP_DIR}"
cp -r mini_agent/config/* "${BACKUP_DIR}/"

# 2. Copy rules file
cp /home/x/Documents/master-mas/TeamADAPT_Rules.md mini_agent/config/

# 3. Set up symlinks
./setup_symlinks.sh

# 4. Test
source activate-portable.sh
mini-agent --version

# 5. Commit changes
git add mini_agent/config/TeamADAPT_Rules.md
git add activate-portable.sh setup_symlinks.sh
git commit -m "Make Mini Agent portable with symlinks"
```

## Deployment on New System

### Scenario: Moving Repository to New Server

```bash
# On old server:
cd /adapt/platform/novaops/frameworks/Minimax-Mini-Agent
tar -czf mini-agent-portable.tar.gz .

# Transfer to new server (scp, rsync, etc.)
scp mini-agent-portable.tar.gz new-server:/tmp/

# On new server:
cd /opt
mkdir mini-agent
cd mini-agent
tar -xzf /tmp/mini-agent-portable.tar.gz

# Create system resources if needed
sudo mkdir -p /adapt/secrets
echo 'MiniMax_M2_CODE_PLAN_API_KEY="your-key"' | sudo tee /adapt/secrets/m2.env

# Set up symlinks
./setup_symlinks.sh

# Activate and run
source activate-portable.sh
### Scenario: Deploying with Systemd\n\n```ini\n# /etc/systemd/system/mini-agent.service\n[Unit]\nDescription=Mini Agent AI Assistant\nAfter=network.target nats-server.service\nWants=nats-server.service\n\n[Service]\nType=simple\nUser=mini-agent\nGroup=mini-agent\nWorkingDirectory=/opt/mini-agent\nExecStart=/bin/bash -c 'source /opt/mini-agent/activate-portable.sh && mini-agent --workspace /opt/mini-agent/workspace'\n\n# Resource limits\nCPUQuota=200%\nMemoryMax=2G\nMemoryHigh=1.5G\n\n# Restart policy\nRestart=on-failure\nRestartSec=30s\n\n# Security\nNoNewPrivileges=true\nPrivateTmp=true\nProtectSystem=strict\nProtectHome=true\nReadWritePaths=/opt/mini-agent /var/log/mini-agent\n\n[Install]\nWantedBy=multi-user.target\n```\n\n```bash\n# Setup on new server:\nsudo apt update\nsudo apt install python3-pip nats-server\n\n# Clone repository\ngit clone <repo-url> /opt/mini-agent\ncd /opt/mini-agent\n\n# Install dependencies\npip3 install uv\nuv sync\n\n# Create directories\nsudo mkdir -p /adapt/secrets /var/log/mini-agent\nsudo chown mini-agent:mini-agent /var/log/mini-agent\n\n# Install Mini Agent\nuv tool install -e .\n\n# Start NATS\nsudo systemctl enable --now nats-server\n\n# Start Mini Agent\nsudo systemctl enable --now mini-agent\n\n# Check status\nsudo systemctl status mini-agent\njournalctl -u mini-agent -f\n```,
```

## Environment Variables

### Portable Mode Configuration

Set these in `activate-portable.sh`:

```bash
# Mini Agent portable mode settings
export MINI_AGENT_PORTABLE_MODE=1
export MINI_AGENT_REPO_DIR="${MINI_AGENT_DIR}"
export MINI_AGENT_SESSIONS_DIR="${MINI_AGENT_DIR}/.agent-sessions"
export MINI_AGENT_RULES_FILE="${MINI_AGENT_DIR}/mini_agent/config/TeamADAPT_Rules.md"
export MINI_AGENT_SECRETS_FILE="${MINI_AGENT_DIR}/.system-symlinks/m2.env"

# Optional: Override default paths
export MINI_AGENT_CUSTOM_CONFIG="${MINI_AGENT_DIR}/my-config.yaml"
export MINI_AGENT_WORKSPACE="${MINI_AGENT_DIR}/workspace"
```

## Troubleshooting

### Problem: Symlink Broken

```bash
# Check if symlink is valid
ls -la .system-symlinks/m2.env

# If broken (shows red), recreate:
rm .system-symlinks/m2.env
ln -s /adapt/secrets/m2.env .system-symlinks/m2.env
```

### Problem: Secrets Not Loading

```bash
# Check if secrets file exists
ls -la .system-symlinks/m2.env

# Check if original file exists
ls -la /adapt/secrets/m2.env

# If not, create test secrets
mkdir -p /adapt/secrets
echo 'MiniMax_M2_CODE_PLAN_API_KEY="test-key"' > /adapt/secrets/m2.env
```

### Problem: Rules Not Loading

```bash
# Check if rules file exists
ls -la mini_agent/config/TeamADAPT_Rules.md

# Check file content
head -10 mini_agent/config/TeamADAPT_Rules.md

# Verify it's being loaded
python3 -c "
from mini_agent.rules_loader import RulesLoader
rl = RulesLoader()
meta = rl.get_rules_metadata()
print(f'Rules loaded: {meta[\"rules_loaded\"]} sections')
"
```

### Problem: Sessions Not Saving

```bash
# Check sessions directory permissions
ls -la .agent-sessions/

# Test write permission
touch .agent-sessions/test.tmp
rm .agent-sessions/test.tmp

# Check disk space
df -h .
```

### Problem: Can't Find Configuration

```bash
# Run diagnostics
cd /adapt/platform/novaops/frameworks/Minimax-Mini-Agent
python3 -c "
from mini_agent.config import Config
config = Config.load()
print(f'Config loaded from: {config}')
print(f'API Base: {config.llm.api_base}')
"

# Check portable mode
source activate-portable.sh
echo $MINI_AGENT_PORTABLE_MODE
```

## Backup and Recovery

### Create Full Backup

```bash
cd /adapt/platform/novaops/frameworks/Minimax-Mini-Agent

BACKUP_NAME="mini-agent-backup-$(date +%Y%m%d-%H%M%S)"

# Create backup
tar -czf "${BACKUP_NAME}.tar.gz" \
    --exclude="__pycache__" \
    --exclude="*.pyc" \
    --exclude=".git" \
    .

# Move to safe location
mv "${BACKUP_NAME}.tar.gz" ~/backups/

echo "Backup created: ~/backups/${BACKUP_NAME}.tar.gz"
```

### Restore from Backup

```bash
# Extract backup
cd /opt
mkdir mini-agent-restored
cd mini-agent-restored
tar -xzf ~/backups/mini-agent-backup-*.tar.gz

# Set up environment
./setup_symlinks.sh
source activate-portable.sh

# Test
mini-agent --version
```

## Production Deployment Checklist

- [ ] Create backup of current state
- [ ] Run `./setup_symlinks.sh`
- [ ] Verify symlinks point to correct locations
- [ ] Copy rules file to repo (if not already present)
- [ ] Test with `source activate-portable.sh && mini-agent`
- [ ] Update systemd service to use portable mode (optional)
- [ ] Document any system dependencies
- [ ] Test full workflow
- [ ] Commit changes to git
- [ ] Create final backup

## Migration Back to System Mode

If you need to revert to system-based deployment:

```bash
cd /adapt/platform/novaops/frameworks/Minimax-Mini-Agent

# 1. Remove local rules copy
rm mini_agent/config/TeamADAPT_Rules.md

# 2. Remove symlinks
rm -rf .system-symlinks
rm .symlinks-config.json

# 3. Reset to system defaults
# (Edit config to use system paths)

# 4. Test
git status  # Check what changed
```

## Summary

**Portable Mini Agent Benefits:**

✅ **Self-contained** - Everything in one directory
✅ **Portable** - Easy to move, backup, deploy
✅ **Flexible** - System resources via symlinks
✅ **Safe** - Revert capability built-in
✅ **Documented** - Clear migration procedures
✅ **No breaking changes** - System mode still works

Your Mini Agent is now fully portable and ready for any deployment scenario!
