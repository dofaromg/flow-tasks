#!/usr/bin/env bash
# MRL Unified System — One-shot boot
# origin_signature: MrLiouWord
set -e

echo "============================================"
echo " MRL Unified System — Boot"
echo " origin_signature: MrLiouWord"
echo "============================================"
echo ""
echo "Services: engine(7700) product(3000) ai(8787) 800ai(8800) bridge(7800)"
echo "          platform/mother(8790) runtimeos(8788) db(5432) redis(6379) nginx(80)"
echo ""

docker compose -f docker-compose.unified.yml up -d --build 2>&1 | sed 's/^/  /'

echo ""
echo "[Health Check] waiting 10s..."
sleep 10

for svc in "engine:7700:/health" "product:3000:/health" "ai:8787:/health" \
           "800ai:8800:/health" "bridge:7800:/health" "platform:8790:/health" \
           "runtimeos:8788:/api/mrl/health" "gateway:80:/health"; do
  name="${svc%%:*}"
  rest="${svc#*:}"
  port="${rest%%:*}"
  path="${rest#*:}"
  status=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:${port}${path}" 2>/dev/null || echo "000")
  if [ "$status" = "200" ]; then
    echo "  mrl-${name} :${port} -> OK"
  else
    echo "  mrl-${name} :${port} -> starting... (HTTP ${status})"
  fi
done

echo ""
echo "============================================"
echo " MRL System Running"
echo ""
echo " Gateway:    http://localhost"
echo " Engine:     http://localhost:7700"
echo " Product:    http://localhost:3000"
echo " AI:         http://localhost:8787"
echo " 800AI:      http://localhost:8800"
echo " Bridge:     http://localhost:7800"
echo " Platform:   http://localhost:8790"
echo " RuntimeOS:  http://localhost:8788"
echo " PostgreSQL: localhost:5432"
echo " Redis:      localhost:6379"
echo ""
echo " Stop:  docker compose -f docker-compose.unified.yml down"
echo " Logs:  docker compose -f docker-compose.unified.yml logs -f"
echo "============================================"
