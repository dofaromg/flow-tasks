# MRL_AI_SYSTEM Deployment Guide

**Origin Signature**: MrLiouWord
**Version**: 2.0
**Status**: P0 Complete (4/5 items)

---

## Quick Start - DL580 Production Deployment

### Prerequisites

1. **Server**: Windows Server or Linux on DL580 hardware
2. **Python**: Python 3.9+ installed
3. **Local LLM**: Ollama or compatible OpenAI-format endpoint at localhost:11434

### Step 1: Clone Repository

```bash
cd /opt
git clone https://github.com/dofaromg/MRL_AI_SYSTEM.git
cd MRL_AI_SYSTEM
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- No external dependencies for core (uses stdlib)
- Optional: `openai`, `anthropic` (if using cloud APIs)

### Step 3: Configure Environment

```bash
# Copy production config template
cp .env.production.example .env

# Edit .env and set:
nano .env
```

**CRITICAL settings**:
```bash
MRL_RUNTIME_MODE=production           # Blocks MockAdapter
MRL_API_REQUIRE_AUTH=true            # Enable auth
MRL_API_AUTH_TOKEN=<your-secure-token>  # Change this!
MRL_LLM_DEFAULT_MODEL=<your-model>   # e.g., "llama2" for Ollama
MRL_LLM_LOCAL_BASE_URL=http://localhost:11434/v1
```

### Step 4: Initialize Data Directories

```bash
# Create required directories
mkdir -p data
mkdir -p 03_memory/_data/memory_chain
mkdir -p 03_memory/vector/_data
```

### Step 5: Verify Configuration

```bash
# Check runtime mode
python 09_workflow/MRL_runtime_config.py check

# Should show:
# Runtime mode: production
# mock         ✗ PROHIBITED
```

### Step 6: Start API Gateway

```bash
# Load environment
source .env

# Start server
python 09_workflow/api_gateway.py --host 0.0.0.0 --port 7771
```

Output should show:
```
[MRL_AGI API] Booting MotherAssembly…
[MRL_AGI API] Subsystems online: 12/12
[MRL_AGI API] Listening on http://0.0.0.0:7771
[MRL_AGI API] origin_signature: MrLiouWord
```

### Step 7: Test Deployment

```bash
# Test health endpoint
curl http://localhost:7771/health

# Test chat endpoint (requires auth token)
curl -X POST http://localhost:7771/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-token>" \
  -d '{
    "message": "Hello, are you working?",
    "model": "llama2"
  }'
```

Expected response includes:
```json
{
  "session_id": "...",
  "reply": "...",
  "model": "llama2",
  "trace_id": "...",
  "engine": "LocalAdapter",
  "runtime_mode": "production",
  "runtime_origin": "DL580_localhost",
  "origin_signature": "MrLiouWord"
}
```

---

## Production Checklist

Before going live, verify:

- [x] **Runtime**: `MRL_RUNTIME_MODE=production` set
- [x] **Auth**: `MRL_API_REQUIRE_AUTH=true` and token configured
- [x] **Model**: `MRL_LLM_DEFAULT_MODEL` is NOT "mock"
- [x] **CORS**: `MRL_API_CORS_ORIGINS` set to specific domains (not "*")
- [ ] **HTTPS**: Reverse proxy (nginx/caddy) with SSL certificate
- [ ] **Firewall**: Port 7771 restricted to trusted IPs
- [ ] **Monitoring**: Log aggregation and alerting configured
- [ ] **Backup**: Data directory backed up regularly

---

## Service Management

### systemd Service (Linux)

Create `/etc/systemd/system/mrl-api.service`:

```ini
[Unit]
Description=MRL_AGI API Gateway
After=network.target

[Service]
Type=simple
User=mrl
WorkingDirectory=/opt/MRL_AI_SYSTEM
EnvironmentFile=/opt/MRL_AI_SYSTEM/.env
ExecStart=/usr/bin/python3 09_workflow/api_gateway.py --host 0.0.0.0 --port 7771
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable mrl-api
sudo systemctl start mrl-api
sudo systemctl status mrl-api
```

### Windows Service

Use NSSM (Non-Sucking Service Manager):

```cmd
nssm install MRL_API python.exe
nssm set MRL_API AppDirectory C:\MRL_AI_SYSTEM
nssm set MRL_API AppParameters "09_workflow\api_gateway.py --host 0.0.0.0 --port 7771"
nssm start MRL_API
```

---

## Nginx Reverse Proxy (Recommended)

Add HTTPS and additional security:

```nginx
server {
    listen 443 ssl http2;
    server_name api.your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req zone=api_limit burst=20 nodelay;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    location / {
        proxy_pass http://127.0.0.1:7771;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (for future streaming)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

---

## Monitoring & Logs

### Access Logs

All access attempts logged to `data/access_log.jsonl`:

```bash
# Monitor access attempts
tail -f data/access_log.jsonl | jq .

# Count denied accesses
grep '"granted":false' data/access_log.jsonl | wc -l
```

### Health Checks

```bash
# Automated health check
*/5 * * * * curl -sf http://localhost:7771/health || systemctl restart mrl-api
```

### Log Rotation

```bash
# /etc/logrotate.d/mrl-api
/opt/MRL_AI_SYSTEM/data/*.jsonl {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 mrl mrl
}
```

---

## Backup Strategy

### Daily Backup

```bash
#!/bin/bash
# /opt/MRL_AI_SYSTEM/backup.sh

BACKUP_DIR="/backup/mrl-$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# Backup data directory
tar -czf "$BACKUP_DIR/data.tar.gz" data/

# Backup memory chain
tar -czf "$BACKUP_DIR/memory.tar.gz" 03_memory/_data/

# Keep only 30 days
find /backup -type d -mtime +30 -exec rm -rf {} +
```

Schedule with cron:
```bash
0 2 * * * /opt/MRL_AI_SYSTEM/backup.sh
```

---

## Troubleshooting

### MockAdapter in Production

**Symptom**: Requests return 403 Forbidden

**Solution**:
```bash
# Check runtime mode
python 09_workflow/MRL_runtime_config.py check

# Should be 'production', not 'development'
# If wrong, set environment variable:
export MRL_RUNTIME_MODE=production

# Or add to .env file
```

### LLM Gateway Unavailable

**Symptom**: "[ERROR] LLMGateway unavailable"

**Solution**:
```bash
# Verify local LLM endpoint is running
curl http://localhost:11434/v1/models

# If Ollama not installed:
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama2
ollama serve
```

### Memory Chain Errors

**Symptom**: merkle chain append failures

**Solution**:
```bash
# Check directory permissions
ls -la 03_memory/_data/

# Should be writable by service user
chmod 755 03_memory/_data/memory_chain
```

### High Memory Usage

**Solution**:
```bash
# Limit conversation sessions
export MRL_CONVERSATION_MAX_SESSIONS=100

# Reduce context window
export MRL_CONTEXT_MAX_TOKENS=2048

# Clear old sessions
python 09_workflow/conversation_manager.py list
# Manually delete old sessions via CLI
```

---

## Upgrade Procedure

### Minor Upgrades (P0 → P1)

```bash
cd /opt/MRL_AI_SYSTEM

# Backup current state
./backup.sh

# Pull updates
git pull origin main

# Check for new dependencies
pip install -r requirements.txt

# Restart service
sudo systemctl restart mrl-api

# Verify
curl http://localhost:7771/health
```

### Major Upgrades

Follow release notes for breaking changes. May require:
- Data migration scripts
- Config updates
- Database schema changes

---

## Security Hardening

### Firewall Rules

```bash
# Allow only specific IPs
ufw allow from 192.168.1.0/24 to any port 7771

# Or use nginx + allow only localhost
ufw allow 443
ufw deny 7771
```

### API Token Rotation

```bash
# Generate new token
NEW_TOKEN=$(openssl rand -hex 32)

# Update .env
sed -i "s/MRL_API_AUTH_TOKEN=.*/MRL_API_AUTH_TOKEN=$NEW_TOKEN/" .env

# Restart service
sudo systemctl restart mrl-api

# Update clients with new token
```

### Audit Trail

```bash
# Review access logs for anomalies
python << EOF
import json
with open('data/access_log.jsonl') as f:
    for line in f:
        entry = json.loads(line)
        if not entry['granted']:
            print(f"DENIED: {entry['user_id']} -> {entry['result_id']}")
EOF
```

---

## Performance Tuning

### Scheduler Workers

```bash
# Increase for high concurrency
export MRL_SCHEDULER_WORKERS=8
```

### Context Window

```bash
# Reduce to improve speed
export MRL_CONTEXT_MAX_TOKENS=2048
export MRL_CONTEXT_REPLY_RESERVE=256
```

### Local Model Optimization

For Ollama:
```bash
# Use quantized models
ollama pull llama2:7b-q4_0

# Adjust threads
OLLAMA_NUM_THREADS=8 ollama serve
```

---

## Production Acceptance Criteria

Before marking deployment complete:

- [x] API gateway starts without errors
- [x] Health endpoint returns 200 OK
- [x] MockAdapter is prohibited in production mode
- [x] All responses include trace metadata
- [x] Authentication is enforced
- [x] Memory tracing is working
- [ ] HTTPS enabled via reverse proxy
- [ ] Monitoring and alerting configured
- [ ] Backup strategy implemented
- [ ] Documentation reviewed by ops team

---

**Next Steps**: See `P1_OPERATIONS.md` for billing, user management, and admin console setup.

**Document Version**: 1.0
**Last Updated**: 2026-05-01
**Origin Signature**: MrLiouWord