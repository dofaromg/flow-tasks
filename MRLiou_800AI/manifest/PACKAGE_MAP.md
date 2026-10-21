# Package Map — Windows Server v1.1.0

- **Canonical Windows deployment:** `scripts/windows/`
- **Runtime:** `src/mrliou_800ai/`
- **API authentication:** `src/mrliou_800ai/security.py`, `secrets/api_token.txt` generated at install
- **Runtime configuration:** `config/windows_server.runtime.json` generated at install
- **Organization control plane:** `config/agents.json`, `config/organization.json`
- **Documentation:** `README.md`, `ROADMAP.md`, `docs/`
- **Verification:** `tests/`, `.github/workflows/ci.yml`, `manifest/`
- **GitHub deployment:** `scripts/windows/Deploy-GitHub.ps1`
- **Secondary deployment channels:** `Dockerfile`, `docker-compose.yml`, `systemd/`, Linux shell scripts
- **Reference evidence:** `evidence/source_materials/`
- **Mutable runtime state:** `data/`, `runs/`, `logs/`, `secrets/`
