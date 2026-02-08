// origin_signature: MrLiouWord
const fs = require('fs');
const { execSync } = require('child_process');

// 獲取所有分支
function getAllBranches() {
  try {
    const branches = execSync('git branch -a', { encoding: 'utf-8' })
      .split('\n')
      .map(b => b.trim().replace('* ', '').replace('remotes/origin/', ''))
      .filter(b => b && !b.includes('HEAD') && !b.includes('->'));
    
    // 去重
    return [...new Set(branches)];
  } catch (error) {
    console.error('Error getting branches:', error.message);
    return ['main'];
  }
}

// 獲取 PR 資訊
function getPRData() {
  try {
    // 檢查 gh CLI 是否可用
    execSync('gh --version', { encoding: 'utf-8' });
    
    const prData = JSON.parse(
      execSync('gh pr list --state all --json number,title,headRefName,state,mergedAt,createdAt --limit 500', 
        { encoding: 'utf-8' })
    );
    return prData;
  } catch (error) {
    console.warn('Warning: gh CLI not available or no PRs found:', error.message);
    return [];
  }
}

// 建立神經網絡
function buildNeuralNetwork() {
  const branches = getAllBranches();
  const prData = getPRData();
  
  const neuralNetwork = {
    origin_signature: "MrLiouWord",
    updated_at: new Date().toISOString(),
    neural_network: {
      nodes: [],
      synapses: []
    }
  };
  
  // 主幹節點
  neuralNetwork.neural_network.nodes.push({
    id: "main",
    type: "trunk",
    layer: "L7",
    frequency_hz: 164.88,
    status: "active",
    energy: 1.0
  });
  
  // 處理每個分支
  branches.forEach(branch => {
    if (branch === 'main') return;
    
    const pr = prData.find(p => p.headRefName === branch);
    
    const node = {
      id: branch,
      type: getBranchType(branch),
      layer: getBranchLayer(branch),
      parent: "main",
      status: pr?.state === "MERGED" ? "merged" : "active",
      energy: pr?.state === "MERGED" ? 0.95 : 0.7
    };
    
    if (pr) {
      node.merged_pr = pr.number;
      node.created_at = pr.createdAt;
      if (pr.mergedAt) {
        node.merged_at = pr.mergedAt;
      }
    }
    
    neuralNetwork.neural_network.nodes.push(node);
    
    // 建立突觸
    neuralNetwork.neural_network.synapses.push({
      from: "main",
      to: branch,
      type: pr?.state === "MERGED" ? "merge" : "influence",
      weight: pr?.state === "MERGED" ? 0.95 : 0.5,
      pr_number: pr?.number,
      timestamp: pr?.mergedAt || pr?.createdAt || new Date().toISOString()
    });
  });
  
  return neuralNetwork;
}

// 判斷分支類型
function getBranchType(branch) {
  if (branch.startsWith('copilot/')) return 'cognitive';
  if (branch.startsWith('feature/')) return 'feature';
  if (branch.startsWith('hotfix/')) return 'hotfix';
  if (branch.startsWith('fix/')) return 'hotfix';
  if (branch.startsWith('experimental/')) return 'experimental';
  return 'experimental';
}

// 判斷分支圖層
function getBranchLayer(branch) {
  const typeLayerMap = {
    'cognitive': 'L6',
    'feature': 'L5',
    'hotfix': 'L4',
    'experimental': 'L3'
  };
  return typeLayerMap[getBranchType(branch)] || 'L3';
}

// 主程序
function main() {
  console.log('🧠 Starting neural network update...');
  
  const network = buildNeuralNetwork();
  
  // 確保目錄存在
  if (!fs.existsSync('neural-links')) {
    fs.mkdirSync('neural-links', { recursive: true });
  }
  
  // 寫入檔案
  fs.writeFileSync(
    'neural-links/branch-map.json',
    JSON.stringify(network, null, 2)
  );
  
  console.log(`✅ Neural network updated: ${network.neural_network.nodes.length} nodes, ${network.neural_network.synapses.length} synapses`);
  console.log(`📊 Active nodes: ${network.neural_network.nodes.filter(n => n.status === 'active').length}`);
  console.log(`✔️  Merged nodes: ${network.neural_network.nodes.filter(n => n.status === 'merged').length}`);
  
  return network;
}

// 執行主程序
if (require.main === module) {
  try {
    main();
  } catch (error) {
    console.error('❌ Error updating neural network:', error.message);
    process.exit(1);
  }
}

module.exports = { buildNeuralNetwork, getBranchType, getBranchLayer };
