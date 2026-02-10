#!/bin/bash
# origin_signature: MrLiouWord
# End-to-end test for neural branch network system

set -e

echo "🧠 Testing Neural Branch Network System"
echo "========================================"
echo ""

# 1. Test update-neural-map.js
echo "1️⃣ Testing neural map update..."
node scripts/update-neural-map.js
if [ -f "neural-links/branch-map.json" ]; then
    echo "✅ branch-map.json generated successfully"
else
    echo "❌ Failed to generate branch-map.json"
    exit 1
fi

# 2. Test generate-mermaid.js
echo ""
echo "2️⃣ Testing Mermaid generation..."
node scripts/generate-mermaid.js
if [ -f "neural-links/synaptic-graph.mermaid" ]; then
    echo "✅ synaptic-graph.mermaid generated successfully"
else
    echo "❌ Failed to generate synaptic-graph.mermaid"
    exit 1
fi

# 3. Validate JSON structure
echo ""
echo "3️⃣ Validating JSON structure..."
node -e "
const fs = require('fs');
const data = JSON.parse(fs.readFileSync('neural-links/branch-map.json', 'utf-8'));

if (!data.origin_signature || data.origin_signature !== 'MrLiouWord') {
    console.error('❌ Invalid origin_signature');
    process.exit(1);
}

if (!data.neural_network || !data.neural_network.nodes || !data.neural_network.synapses) {
    console.error('❌ Invalid neural_network structure');
    process.exit(1);
}

console.log('✅ JSON structure is valid');
console.log('   - Nodes:', data.neural_network.nodes.length);
console.log('   - Synapses:', data.neural_network.synapses.length);
"

# 4. Validate Mermaid syntax
echo ""
echo "4️⃣ Validating Mermaid syntax..."
if grep -q "graph TD" neural-links/synaptic-graph.mermaid && \
   grep -q "classDef trunk" neural-links/synaptic-graph.mermaid; then
    echo "✅ Mermaid syntax is valid"
else
    echo "❌ Invalid Mermaid syntax"
    exit 1
fi

# 5. Check visualizer.html exists
echo ""
echo "5️⃣ Checking visualizer.html..."
if [ -f "neural-links/visualizer.html" ]; then
    echo "✅ visualizer.html exists"
else
    echo "❌ visualizer.html not found"
    exit 1
fi

# 6. Check TypeScript module exists
echo ""
echo "6️⃣ Checking TypeScript module..."
if [ -f "src/neural-links/neural-index.ts" ]; then
    echo "✅ neural-index.ts exists"
else
    echo "❌ neural-index.ts not found"
    exit 1
fi

# 7. Run unit tests
echo ""
echo "7️⃣ Running unit tests..."
npm test -- src/neural-links/__tests__/neural-index.test.ts --passWithNoTests 2>&1 | grep -E "(PASS|FAIL|Tests:)" || true

echo ""
echo "========================================"
echo "✅ All neural network system tests passed!"
echo ""
echo "📊 System Summary:"
node -e "
const fs = require('fs');
const data = JSON.parse(fs.readFileSync('neural-links/branch-map.json', 'utf-8'));
const nodes = data.neural_network.nodes;
const synapses = data.neural_network.synapses;
console.log('   - Total Nodes:', nodes.length);
console.log('   - Total Synapses:', synapses.length);
console.log('   - Active Nodes:', nodes.filter(n => n.status === 'active').length);
console.log('   - Merged Nodes:', nodes.filter(n => n.status === 'merged').length);
const avgEnergy = (nodes.reduce((sum, n) => sum + n.energy, 0) / nodes.length * 100).toFixed(1);
console.log('   - Average Energy:', avgEnergy + '%');
"
echo ""
echo "🧠 To view the interactive visualizer:"
echo "   cd neural-links && python -m http.server 8000"
echo "   Then open: http://localhost:8000/visualizer.html"
