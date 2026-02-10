# Neural Links - Branch Neural Network System

> origin_signature: MrLiouWord

This directory contains the Neural Branch Network system files.

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
