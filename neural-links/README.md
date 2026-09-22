# Neural Links - Branch Neural Network System

> origin_signature: MrLiouWord

This directory contains the Neural Branch Network system files.

## MRL canonical naming policy

All automatically expanded graph identities use the canonical `MRL_` prefix.

| Graph field | Rule |
|---|---|
| `node.id` | Canonical MRL identity; always begins with `MRL_` |
| `node.source_branch` | Exact Git branch name; preserved without mutation |
| `synapse.from/to` | Reference canonical MRL node IDs |
| Mermaid/D3 label | Displays the canonical MRL identity |

Example: Git branch `copilot/example` becomes graph node `MRL_copilot/example`, while `source_branch` remains `copilot/example`.

Generation fails if a node lacks the prefix, loses `source_branch`, duplicates a canonical ID, or creates an unresolved synapse. Existing Git branches are not renamed.

Enforcement order: normalize source identity → validate canonical naming and provenance → render JSON/Mermaid → commit generated evidence.

Integrity gates also reject canonical/source mismatches, unresolved synapses, and Mermaid identifier collisions.

## Files

### branch-map.json
The main data file containing the neural network structure with nodes (branches) and synapses (connections).

Auto-updated by GitHub Actions on every push or PR merge.

### synaptic-graph.mermaid
Mermaid diagram visualization of the branch neural network.

Auto-generated from `branch-map.json`.

### visualizer.html
Interactive HTML visualizer powered by D3.js.

Open this file in a browser to explore the branch neural network interactively.

## Quick Start

### View the visualizer locally

```bash
cd neural-links
python -m http.server 8000
# or
npx http-server
```

Then open http://localhost:8000/visualizer.html

### Update the network manually

```bash
# From repository root
node scripts/update-neural-map.js
node scripts/generate-mermaid.js
```

## Features

- 🧠 Neural network representation of Git branches
- 📊 Interactive D3.js visualization
- 🎨 Mermaid diagram generation
- 🔄 Automatic synchronization via GitHub Actions
- 📈 Branch influence calculation
- 🔍 Path tracing between branches
- 🎯 Layer-based filtering

For detailed documentation, see [BRANCH_NEURAL_MAP.md](../BRANCH_NEURAL_MAP.md)
