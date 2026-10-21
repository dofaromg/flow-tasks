# Acceptance Matrix

| Check | PASS 條件 |
|---|---|
| health | `/api/health` returns ok |
| upload | upload writes file + manifest |
| scan list | `/api/scans` returns scan metadata |
| job create | job record created |
| job status | status query returns job |
| runner | mrl3d/COLMAP run or explicit failed reason |
| no fake | failed tools are not marked completed |
| report | acceptance report written |
