# Private Experiments Area
# 私有實驗區域

This directory contains private experimental scenarios and data for the Particle Satellite Network system.

## ⚠️ Important

**All data in the `data/` and `results/` subdirectories is excluded from version control.**

## Directory Structure

```
experiments/
├── scenarios/          # Experimental scenarios (Python scripts)
├── data/              # Experimental data (NOT committed)
├── results/           # Experimental results (NOT committed)
└── .gitignore         # Protects private data
```

## Running Experiments

```bash
# Run a specific scenario
python scenarios/scenario_01_basic_mesh.py

# Or use the experiment runner
python ../scripts/run_experiment.py --scenario 1
```

## Creating New Experiments

1. Create a new Python file in `scenarios/`
2. Implement your experimental logic
3. Results will be saved to `results/` automatically
4. Data files go to `data/`

## Example Scenario Structure

```python
# scenarios/scenario_example.py

import asyncio
from particle_satellite_network.core import *

async def run_experiment():
    # Your experiment logic here
    pass

if __name__ == "__main__":
    asyncio.run(run_experiment())
```

## Security

- Never commit sensitive data
- Keep experiment results local
- Use environment variables for secrets
- Review files before committing

---

**Note**: This is a private experimental area. Handle data with care.
