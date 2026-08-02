# 05_persona

Persona definitions and world module for MrLiouAI agents (L4 WORLD / L5 MIRROR layer).

## Files

| File | Purpose |
|------|---------|
| `world_module.py` | World Module entry point — nodes, state, trajectory, particle-globe coordinates |
| `codepartner/persona.yaml` | CodePartner (CoreProgrammer.Seed) — recovered MrLiouAI programming persona |

## world_module.py

Official entry point for the WorldModule core group (Y=4).
Manages memory-particle nodes, key-value world state, ordered trajectory history,
and particle-globe coordinates for 3-D visualisation.

```bash
# Set a world node
python 05_persona/world_module.py set --node FlowSeed --data '{"type":"persona","layer":"L1"}'

# Read it back
python 05_persona/world_module.py get --node FlowSeed

# Set a world-state key
python 05_persona/world_module.py state --key active_persona --value FlowSeed

# Full snapshot
python 05_persona/world_module.py snap

# Attach particle-globe coordinates
python 05_persona/world_module.py globe --node FlowSeed --lat 25.0 --lon 121.5

# Rewind trajectory by 1 step
python 05_persona/world_module.py rewind --step 1
```

Runtime data is written to `05_persona/_data/world/` (gitignored).

## Persona definition format

```yaml
id: <persona_id>
name: <human-readable name>
layer: L4
capabilities: []        # allowed action types
constraints: []         # extra rules beyond rootlaw
world: AI | Platform | Real
```

First implemented persona: `codepartner/persona.yaml` (CodePartner / CoreProgrammer.Seed,
recovered from the MrLiouAI lineage — sources in `08_sources/mrliouai_codepartner_recovery/`).

See `00_rootlaw/rootlaw.yaml` for invariants that apply to all personas.

