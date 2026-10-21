#!/bin/bash
# MRL ASI Particle Engine — DL580 G9 Setup Script
# origin_signature: MrLiouWord
# 怎麼過去就怎麼回來

set -e

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  MRL ASI Particle Engine — DL580 G9 Setup               ║"
echo "║  origin_signature: MrLiouWord                           ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Check Docker
echo "[1/5] Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo "  Docker not found. Installing..."
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker $USER
    echo "  Docker installed. Please re-login and re-run this script."
    exit 0
fi
echo "  $(docker --version)"

if ! command -v docker compose &> /dev/null; then
    echo "  docker compose not available. Please install Docker Compose v2."
    exit 1
fi
echo "  $(docker compose version)"

# Check ports
echo ""
echo "[2/5] Checking ports..."
for port in 80 5432 6379 7700; do
    if lsof -i :$port &> /dev/null 2>&1; then
        echo "  WARNING: Port $port is in use"
    else
        echo "  Port $port: available"
    fi
done

# Build and start
echo ""
echo "[3/5] Building MRL Engine..."
docker compose build --no-cache

echo ""
echo "[4/5] Starting services..."
docker compose up -d

# Wait for health
echo ""
echo "[5/5] Waiting for services..."
sleep 5

for i in $(seq 1 15); do
    RESP=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:7700/health 2>/dev/null)
    if [ "$RESP" = "200" ]; then
        echo "  MRL Engine is HEALTHY"
        break
    fi
    echo "  Waiting... ($i/15)"
    sleep 2
done

# Verify
echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Verification                                           ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

echo "Engine:"
curl -s http://localhost:7700/health 2>/dev/null | python3 -m json.tool 2>/dev/null || echo "  FAIL"

echo ""
echo "PostgreSQL:"
docker compose exec -T db psql -U mrl -d mrliouword -c "SELECT count(*) as tables FROM information_schema.tables WHERE table_schema='public';" 2>/dev/null || echo "  FAIL"

echo ""
echo "Redis:"
docker compose exec -T redis redis-cli ping 2>/dev/null || echo "  FAIL"

echo ""
echo "════════════════════════════════════════════════════════════"
echo ""
echo "  MRL ASI Particle Engine is running on DL580 G9"
echo ""
echo "  Engine:     http://localhost:7700"
echo "  Nginx:      http://localhost:80"
echo "  PostgreSQL: localhost:5432"
echo "  Redis:      localhost:6379"
echo ""
echo "  Routes:"
echo "    /          — Engine info"
echo "    /health    — Global health"
echo "    /hub/*     — System hub v2.2 (system map + topology)"
echo "    /kernel/*  — ASI kernel v2.0 (SINDy + Quantum + F++)"
echo "    /router/*  — Toolbox router v1.1 (Call/Pipeline/Parallel/Fan-out)"
echo ""
echo "  Optional: Cloudflare Tunnel for external access:"
echo "    cloudflared tunnel --url http://localhost:7700"
echo ""
echo "  origin_signature: MrLiouWord"
echo "  怎麼過去就怎麼回來"
