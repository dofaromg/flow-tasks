#!/bin/bash
# FlowAgent 部署驗證腳本
# 用於驗證 Kubernetes 配置檔案的正確性

set -e

echo "========================================="
echo "FlowAgent 部署配置驗證"
echo "========================================="
echo ""

# 檢查必要工具
echo "[1/5] 檢查必要工具..."
command -v kubectl >/dev/null 2>&1 || { echo "錯誤: kubectl 未安裝"; exit 1; }
command -v kustomize >/dev/null 2>&1 || { echo "錯誤: kustomize 未安裝"; exit 1; }
echo "✅ 工具檢查完成"
echo ""

# 驗證 YAML 語法
echo "[2/5] 驗證 YAML 檔案語法..."
for file in $(find apps cluster argocd -name "*.yaml" -o -name "*.yml"); do
    if ! kubectl apply --dry-run=client -f "$file" >/dev/null 2>&1; then
        echo "❌ 語法錯誤: $file"
        kubectl apply --dry-run=client -f "$file"
        exit 1
    fi
    echo "  ✓ $file"
done
echo "✅ YAML 語法驗證完成"
echo ""

# 驗證 Kustomize 配置
echo "[3/5] 驗證 Kustomize 配置..."
if kustomize build cluster/overlays/prod > /tmp/kustomize-output.yaml 2>&1; then
    echo "✅ Kustomize 建置成功"
    echo "  輸出檔案: /tmp/kustomize-output.yaml"
    echo "  資源數量: $(grep -c '^---' /tmp/kustomize-output.yaml || echo "1")"
else
    echo "❌ Kustomize 建置失敗"
    kustomize build cluster/overlays/prod
    exit 1
fi
echo ""

# 檢查映像參考
echo "[4/5] 檢查容器映像參考..."
grep -r "image:" apps/ cluster/ | grep -v "^#" | while read -r line; do
    echo "  $line"
done
echo "✅ 映像參考檢查完成"
echo ""

# 列出將要建立的資源
echo "[5/5] 列出將要建立的資源..."
kubectl apply --dry-run=client -k cluster/overlays/prod
echo ""

echo "========================================="
echo "✅ 所有驗證通過！"
echo "========================================="
echo ""
echo "下一步："
echo "1. 如果還沒有 GKE 叢集，執行: bash scripts/oneclick_gke_init.sh"
echo "2. 部署到叢集: kubectl apply -k cluster/overlays/prod"
echo "3. 查看狀態: kubectl get all -n flowagent"
echo ""
