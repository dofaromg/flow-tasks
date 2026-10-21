# Architecture

```text
External request / GitHub / local operator
                 │
                 ▼
         Engineering Wake Gate
 collect → compare → plan → execute → verify
                 │
                 ▼
          Agent Orchestrator
 architect / engineer / reviewer / optimizer
 debugger / refactorer / UI / physics audit
                 │
        ┌────────┴────────┐
        ▼                 ▼
 Reversible Store     Physics Audit
 snapshot + SHA       CFD field operators
 trace chain           conservation residuals
        └────────┬────────┘
                 ▼
       Evidence / runs / reports
```

The 800 agents are logical role instances. The runtime multiplexes them over available local model and execution resources instead of requiring 800 simultaneously resident LLM processes.
