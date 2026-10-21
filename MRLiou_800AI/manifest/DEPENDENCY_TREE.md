# Dependency Tree — Windows Server v1.1.0

```text
Windows Server PowerShell entrypoints
├── scripts/windows/Install-WindowsServer.ps1
│   ├── Common.ps1
│   ├── Verify-WindowsServer.ps1
│   ├── Register-StartupTask.ps1
│   └── Open-Firewall.ps1
├── scripts/windows/Start-Runtime.ps1
│   └── python -m mrliou_800ai.cli serve
├── scripts/windows/Get-RuntimeStatus.ps1
├── scripts/windows/Backup-Runtime.ps1
└── scripts/windows/Deploy-GitHub.ps1
    ├── Verify-WindowsServer.ps1
    ├── git.exe
    └── gh.exe

Python runtime
├── cli.py
│   ├── api.py
│   │   └── security.py
│   ├── registry.py
│   ├── orchestrator.py
│   │   ├── audit.py
│   │   └── trace.py
│   ├── datastore.py
│   └── physics/pipeline.py
│       └── conservation.py
│           └── operators.py
├── config/agents.json
├── config/organization.json
└── tests/
```
