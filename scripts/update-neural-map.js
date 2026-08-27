// origin_signature: MrLiouWord
const fs = require('fs');
const { execSync } = require('child_process');

const MRL_NAMING_PREFIX = 'MRL_';

function toMRLNodeId(sourceIdentity) {
  if (typeof sourceIdentity !== 'string' || !sourceIdentity.trim()) {
    throw new Error('MRL naming requires a non-empty source identity');
  }

  const trimmed = sourceIdentity.trim();
  if (/^MRL_/i.test(trimmed)) {
    const suffix = trimmed.slice(MRL_NAMING_PREFIX.length);
    if (!suffix) {
      throw new Error('MRL naming requires content after the MRL_ prefix');
    }
    return `${MRL_NAMING_PREFIX}${suffix}`;
  }

  return `${MRL_NAMING_PREFIX}${trimmed}`;
}

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
  const canonicalIds = new Set();
  const rootId = toMRLNodeId('main');
  canonicalIds.add(rootId);
  
  const neuralNetwork = {
    origin_signature: "MrLiouWord",
    naming_policy: {
      version: "MRL_AutoExpansion_Naming_v1",
      canonical_prefix: MRL_NAMING_PREFIX,
      canonical_identity_field: "id",
      source_identity_field: "source_branch",
      source_identity_mutated: false
    },
    updated_at: new Date().toISOString(),
    neural_network: {
      nodes: [],
      synapses: []
    }
  };
  
  // 主幹節點
  neuralNetwork.neural_network.nodes.push({
    id: rootId,
    source_branch: "main",
    naming_authority: "MRL",
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
    const canonicalId = toMRLNodeId(branch);

    if (canonicalIds.has(canonicalId)) {
      throw new Error(`MRL canonical identity collision: ${canonicalId} from source branch ${branch}`);
    }
    canonicalIds.add(canonicalId);
    
    const node = {
      id: canonicalId,
      source_branch: branch,
      naming_authority: "MRL",
      type: getBranchType(branch),
      layer: getBranchLayer(branch),
      parent: rootId,
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
      from: rootId,
      to: canonicalId,
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

module.exports = { MRL_NAMING_PREFIX, toMRLNodeId, buildNeuralNetwork, getBranchType, getBranchLayer };
