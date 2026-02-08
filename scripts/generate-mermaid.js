// origin_signature: MrLiouWord
const fs = require('fs');

// 清理節點 ID 使其符合 Mermaid 語法
function sanitizeId(id) {
  return id.replace(/[\/\-\.]/g, '_');
}

// 生成 Mermaid 圖
function generateMermaidGraph(data) {
  let mermaid = "```mermaid\n";
  mermaid += "graph TD\n";
  
  // 添加註解
  mermaid += "  %% 神經網絡分支圖譜 - origin_signature: MrLiouWord\n\n";
  
  // 生成節點
  mermaid += "  %% 節點定義\n";
  data.neural_network.nodes.forEach(node => {
    const nodeId = sanitizeId(node.id);
    const label = `${node.id}<br/>${node.layer}`;
    const prInfo = node.merged_pr ? ` #${node.merged_pr}` : '';
    const statusIcon = node.status === 'merged' ? '✓' : node.status === 'active' ? '●' : '○';
    
    mermaid += `  ${nodeId}["${statusIcon} ${label}${prInfo}"]:::${node.type}\n`;
  });
  
  mermaid += "\n  %% 連結定義\n";
  
  // 生成連結
  data.neural_network.synapses.forEach(synapse => {
    const fromId = sanitizeId(synapse.from);
    const toId = sanitizeId(synapse.to);
    
    let linkType;
    let linkLabel = synapse.type;
    
    if (synapse.type === 'merge') {
      linkType = '-->|merged|';
    } else if (synapse.type === 'influence') {
      linkType = '-.->|active|';
    } else {
      linkType = `-.->|${synapse.type}|`;
    }
    
    mermaid += `  ${fromId} ${linkType} ${toId}\n`;
  });
  
  mermaid += "\n  %% 樣式定義\n";
  mermaid += "  classDef trunk fill:#ff6b6b,stroke:#333,stroke-width:4px,color:#fff\n";
  mermaid += "  classDef cognitive fill:#4ecdc4,stroke:#333,stroke-width:3px,color:#000\n";
  mermaid += "  classDef feature fill:#95e1d3,stroke:#333,stroke-width:2px,color:#000\n";
  mermaid += "  classDef hotfix fill:#f9ca24,stroke:#333,stroke-width:2px,color:#000\n";
  mermaid += "  classDef experimental fill:#6c5ce7,stroke:#333,stroke-width:2px,color:#fff\n";
  
  mermaid += "```";
  
  return mermaid;
}

// 主程序
function main() {
  console.log('🎨 Generating Mermaid diagram...');
  
  // 讀取神經網絡資料
  let data;
  try {
    data = JSON.parse(fs.readFileSync('neural-links/branch-map.json', 'utf-8'));
  } catch (error) {
    console.error('❌ Error reading branch-map.json:', error.message);
    console.log('💡 Run update-neural-map.js first to generate the neural network data.');
    process.exit(1);
  }
  
  // 生成 Mermaid 圖
  const mermaidGraph = generateMermaidGraph(data);
  
  // 確保目錄存在
  if (!fs.existsSync('neural-links')) {
    fs.mkdirSync('neural-links', { recursive: true });
  }
  
  // 寫入檔案
  fs.writeFileSync('neural-links/synaptic-graph.mermaid', mermaidGraph);
  
  console.log('✅ Mermaid diagram generated successfully!');
  console.log(`📊 Nodes: ${data.neural_network.nodes.length}, Synapses: ${data.neural_network.synapses.length}`);
}

// 執行主程序
if (require.main === module) {
  try {
    main();
  } catch (error) {
    console.error('❌ Error generating Mermaid diagram:', error.message);
    process.exit(1);
  }
}

module.exports = { generateMermaidGraph, sanitizeId };
