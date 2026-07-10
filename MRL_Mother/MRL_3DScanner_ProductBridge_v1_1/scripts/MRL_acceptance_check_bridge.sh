#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPORT_DIR="$ROOT/acceptance_reports"
mkdir -p "$REPORT_DIR"
REPORT="$REPORT_DIR/MRL_acceptance_bridge_$(date +%Y%m%d_%H%M%S).md"
line(){ echo "$*" | tee -a "$REPORT"; }

TMP="${TMPDIR:-/tmp}/mrl_bridge_cube.obj"
cat > "$TMP" <<'OBJ'
v -0.5 -0.5 -0.5
v 0.5 -0.5 -0.5
v 0.5 0.5 -0.5
v -0.5 0.5 -0.5
v -0.5 -0.5 0.5
v 0.5 -0.5 0.5
v 0.5 0.5 0.5
v -0.5 0.5 0.5
f 1 2 3
f 1 3 4
f 5 8 7
f 5 7 6
f 1 5 6
f 1 6 2
f 2 6 7
f 2 7 3
f 3 7 8
f 3 8 4
f 4 8 5
f 4 5 1
OBJ

line "# MRL 3DScanner Bridge Acceptance"
line "time: $(date -Iseconds)"
if curl -fsS http://localhost:3050/api/health >/tmp/mrl_health.json; then line "health: PASS"; else line "health: FAIL"; exit 1; fi
curl -fsS -X POST http://localhost:3050/api/scans/upload \
  -H 'X-MRL-Scan-ID: acceptance_mesh' \
  -H 'X-MRL-Scan-Name: acceptance_mesh' \
  -F "files=@$TMP" >/tmp/mrl_upload.json
line "upload: PASS"
curl -fsS -X POST http://localhost:3050/api/reconstruction/jobs \
  -H 'Content-Type: application/json' \
  -d '{"scanId":"acceptance_mesh","mode":"auto"}' >/tmp/mrl_job.json
JOB_ID="$(python3 - <<'PY'
import json
print(json.load(open('/tmp/mrl_job.json'))['jobId'])
PY
)"
line "job_create: PASS jobId=$JOB_ID"
for i in $(seq 1 30); do
  sleep 2
  curl -fsS "http://localhost:3050/api/reconstruction/jobs/$JOB_ID" >/tmp/mrl_status.json
  STATUS="$(python3 - <<'PY'
import json
print(json.load(open('/tmp/mrl_status.json')).get('status'))
PY
)"
  [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ] && break
done
MESSAGE="$(python3 - <<'PY'
import json
j=json.load(open('/tmp/mrl_status.json'))
print(j.get('message') or '')
PY
)"
if [ "$STATUS" = "completed" ]; then
  line "runner: PASS"
  line "reason: $MESSAGE"
  line "ACCEPTANCE PASS"
else
  line "runner: FAIL status=$STATUS"
  line "failed reason: $MESSAGE"
  exit 1
fi
