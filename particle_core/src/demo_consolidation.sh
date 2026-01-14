#!/bin/bash
# 記憶種子合併示範腳本
# Memory Seeds Consolidation Demo Script

echo "============================================================"
echo "記憶種子合併工具 - 完整示範"
echo "Memory Seeds Consolidation Tool - Complete Demo"
echo "============================================================"
echo ""

# 進入正確的目錄
cd "$(dirname "$0")"

echo "📍 當前目錄: $(pwd)"
echo ""

echo "步驟 1: 創建 25 個測試種子"
echo "Step 1: Creating 25 sample seeds"
echo "------------------------------------------------------------"
python create_sample_seeds.py --count 25
echo ""

echo "步驟 2: 列出所有種子"
echo "Step 2: List all seeds"
echo "------------------------------------------------------------"
python consolidate_memory_seeds.py --list | head -15
echo "... (完整列表略)"
echo ""

echo "步驟 3: 模擬合併至 10 個種子"
echo "Step 3: Simulate consolidation to 10 seeds"
echo "------------------------------------------------------------"
python consolidate_memory_seeds.py --target 10 --dry-run
echo ""

echo "是否執行實際合併? (y/n)"
echo "Proceed with actual consolidation? (y/n)"
read -p "> " answer

if [ "$answer" = "y" ] || [ "$answer" = "Y" ]; then
    echo ""
    echo "步驟 4: 執行合併"
    echo "Step 4: Execute consolidation"
    echo "------------------------------------------------------------"
    python consolidate_memory_seeds.py --target 10
    echo ""
    
    echo "步驟 5: 驗證結果"
    echo "Step 5: Verify results"
    echo "------------------------------------------------------------"
    echo "合併後的種子列表:"
    python consolidate_memory_seeds.py --list | grep "consolidated_"
    echo ""
    
    echo "✅ 示範完成！"
    echo "✅ Demo completed!"
else
    echo ""
    echo "已取消合併操作"
    echo "Consolidation cancelled"
fi

echo ""
echo "============================================================"
echo "提示: 查看詳細文檔"
echo "Tip: Check detailed documentation"
echo "------------------------------------------------------------"
echo "  particle_core/docs/consolidation_guide.md"
echo "============================================================"
