# Agent Production Guide

> A Complete Guide from Demo to Production

## Table of Contents

- [1. Demo Features](#1-demo-features)
- [2. Upgrade Directions](#2-upgrade-directions)
- [3. Production Deployment](#3-production-deployment)
- [4. NATS Configuration](#4-nats-configuration)

---

## 1. Demo Features

This project is a **teaching-level demo** that demonstrates the core concepts and execution flow of an Agent. To reach production level, many complex issues still need to be addressed.

### What We've Implemented (Demo Level)

| Feature                  | Demo Implementation                   |
| --------------------- | --------------------------- |
| **Context Management** | ✅ Simple persistence via SessionNoteTool with file storage; basic summarization when approaching context window limit |
| **Tool Calling**          | ✅ Basic Read/Write/Edit/Bash |
| **Error Handling**          | ✅ Basic exception catching              |
| **Logging**              | ✅ Simple print output           |


## 2. Upgrade Directions

### 2.1 Advanced Context Management

- Introduce distributed file systems for unified context persistence management and backup
- Use more precise methods for token counting
- Introduce more strategies for message compression, including keeping the most recent N messages, preserving fixed metadata, prompt optimization for summarization, introducing recall systems, etc.

### 2.2 Model Fallback Mechanism

Currently using a single fixed model (MiniMax-M2), which will directly report errors on failure.

- Introduce a model pool by configuring multiple model accounts to improve availability
- Introduce automatic health checks, failure removal, circuit breaker strategies for the model pool

### 2.3 Model Hallucination Detection and Correction

Currently directly trusts model output without validation mechanism

- Perform security checks on input parameters for certain tool calls to prevent high-risk actions
- Perform reflection on results from certain tool calls to check if they are reasonable

### 2.4 A2A Communication with NATS

Agent-to-Agent communication is now handled via NATS for lightweight, high-performance messaging.

- **NATS Setup**: See [NATS Configuration](#nats-configuration)
- **Self-Modifications**: All code changes require approval via A2A
- **Audit Trail**: Complete logging via NATS-backed messaging

## 3. Production Deployment

### 3.1 Systemd Deployment (Recommended)

**No Docker or venv required** - deploy directly with systemd for production:

- **Resource Control**: Limit CPU, memory, and disk usage per service
- **Auto-Restart**: Automatic restart on failure
- **Logging**: Integrated with system journal
- **Dependencies**: Define service dependencies

### 3.2 Resource Limit Configuration

#### 3.2.1 CPU and Memory Limits (systemd)

```ini
# /etc/systemd/system/mini-agent.service
[Unit]
Description=Mini Agent AI Assistant
After=network.target nats-server.service
Requires=nats-server.service

[Service]
Type=simple
User=mini-agent
Group=mini-agent
WorkingDirectory=/opt/mini-agent
ExecStart=/usr/local/bin/mini-agent --workspace /opt/mini-agent/workspace

# Resource limits
CPUQuota=200%                    # Maximum 2 CPU cores
MemoryMax=2G                     # Maximum 2GB RAM
MemoryHigh=1.5G                  # Start throttling at 1.5GB

# Restart policy
Restart=on-failure
RestartSec=30s
StartLimitInterval=60s
StartLimitBurst=3

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/mini-agent /var/log/mini-agent

[Install]
WantedBy=multi-user.target
```

#### 3.2.2 Disk Limits (systemd)

```ini
# Add to [Service] section
SystemCallFilter=@system-service
SystemCallErrorNumber=EPERM
ReadWritePaths=/opt/mini-agent /var/log/mini-agent
# Limit temporary files
PrivateTmp=true
TmpfsSize=1G                     # Limit temp files to 1GB
```

### 3.3 Security Hardening (Production)

#### 3.3.1 Service User Configuration

```bash
# Create dedicated user (no login, no shell)
sudo useradd -r -s /bin/false mini-agent

# Set permissions
sudo chown -R mini-agent:mini-agent /opt/mini-agent /home/mini-agent/.mini-agent
sudo chmod 750 /opt/mini-agent
```

#### 3.3.2 File System Permissions

```bash
# Protect critical files
sudo chmod 600 /opt/mini-agent/mini_agent/config/config.yaml
sudo chown mini-agent:mini-agent /opt/mini-agent/mini_agent/config/config.yaml
sudo chmod 600 /adapt/secrets/m2.env

# Ensure logs are writable
sudo mkdir -p /var/log/mini-agent
sudo chown mini-agent:mini-agent /var/log/mini-agent
sudo chmod 755 /var/log/mini-agent
```

### 3.4 NATS Integration for A2A

For production, NATS should be configured with authentication and TLS:

```ini
# /etc/nats/nats-server.conf
# System-level NATS configuration

listen: 0.0.0.0:4222

# Authentication
authorization: {
  users: [
    {user: "agent_user", password: "$AGENT_NATS_PASSWORD"}
  ]
}

# TLS (for production)
# tls: {
#   cert_file: "/etc/nats/server.pem"
#   key_file: "/etc/nats/server-key.pem"
# }

# Logging
log: "/var/log/nats/nats.log"
log_size_limit: 10MB

# Limits
max_connections: 100
max_subscriptions: 1000
ping_interval: 2
ping_max: 3
```

Start NATS as a systemd service:
```bash
sudo systemctl enable nats-server
sudo systemctl start nats-server
```

### 3.5 Monitoring and Logging

### 3.2 Resource Limit Configuration

#### 3.2.1 CPU and Memory Limits

To prevent the Agent from consuming excessive CPU/Memory resources and affecting the host, CPU and memory limits must be set:

**Docker Configuration Example**:
```yaml
# docker-compose.yml
services:
  agent:
    image: agent-demo:latest
    deploy:
      resources:
        limits:
          cpus: '2.0'      # Maximum 2 CPU cores
          memory: 2G       # Maximum 2GB memory
        reservations:
          cpus: '0.5'      # Guarantee at least 0.5 cores
          memory: 512M     # Guarantee at least 512MB
```

#### 3.2.2 Disk Limits

Agents may generate large amounts of temporary files and log files, so disk usage needs to be limited:

**Docker Volume Configuration**:
```yaml
# docker-compose.yml
services:
  agent:
    volumes:
      - type: tmpfs
        target: /tmp
        tmpfs:
          size: 1G         # Maximum 1GB for temporary files
      - type: volume
        source: agent-data
        target: /app/data
        volume:
          driver_opts:
            size: 5G       # Maximum 5GB for data volume
```


### 3.3 Linux Account Permission Restrictions

#### 3.3.1 Principle of Least Privilege

**Never run the Agent as root user**, as this poses serious security risks.

**Dockerfile Best Practices**:
```dockerfile
FROM python:3.11-slim

# Install necessary system tools
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Create non-privileged user
RUN groupadd -r agent && useradd -r -g agent agent

# Set working directory
WORKDIR /app

# Option 1: Clone from Git repository (for public repos)
RUN git clone https://github.com/MiniMax-AI/agent-demo.git . && \
    chown -R agent:agent /app

# Option 2: Copy code from local (for private deployments)
# COPY --chown=agent:agent . /app

# Switch to non-privileged user before installing dependencies
USER agent

# Sync dependencies using uv
RUN uv sync

# Start the application
CMD ["uv", "run", "python", "main.py"]
```

#### 3.3.2 File System Permissions

Restrict the Agent to only access necessary directories:

```bash
# Create restricted workspace directory
mkdir -p /app/workspace
chown agent:agent /app/workspace
chmod 750 /app/workspace  # Owner: read/write/execute, Group: read/execute

# Restrict access to sensitive directories
chmod 700 /etc/agent      # Config directory only accessible by owner
chmod 600 /etc/agent/*.yaml  # Config files only readable/writable by owner
```

