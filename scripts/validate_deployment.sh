#!/bin/bash
# FlowAgent 部署驗證腳本
# 用於驗證 Kubernetes 配置檔案的正確性

set -e

echo "========================================="
echo "FlowAgent 部署配置驗證"
echo "========================================="
echo ""

# 檢查必要工具
echo "[1/4] 檢查必要工具..."
command -v kubectl >/dev/null 2>&1 || { echo "錯誤: kubectl 未安裝"; exit 1; }
command -v kustomize >/dev/null 2>&1 || { echo "錯誤: kustomize 未安裝"; exit 1; }
echo "✅ 工具檢查完成"
echo ""

# 驗證 YAML 語法 (使用 Python yaml 模組)
echo "[2/4] 驗證 YAML 檔案語法..."
if command -v python3 >/dev/null 2>&1; then
    for file in $(find apps cluster argocd -name "*.yaml" -o -name "*.yml"); do
        if ! python3 -c "import yaml; list(yaml.safe_load_all(open('$file')))" 2>/dev/null; then
            echo "❌ 語法錯誤: $file"
            python3 -c "import yaml; list(yaml.safe_load_all(open('$file')))"
            exit 1
        fi
        echo "  ✓ $file"
    done
    echo "✅ YAML 語法驗證完成"
else
    echo "⚠️  Python 未安裝，跳過 YAML 語法驗證"
fi
echo ""

# 驗證 Kustomize 配置
echo "[3/4] 驗證 Kustomize 配置..."
echo "  → 建置 Production overlay..."
if kustomize build cluster/overlays/prod > /tmp/kustomize-prod.yaml 2>&1; then
    echo "  ✅ Production 建置成功"
    echo "     資源數量: $(grep -c '^---' /tmp/kustomize-prod.yaml || echo "1")"
else
    echo "  ❌ Production 建置失敗"
    kustomize build cluster/overlays/prod
    exit 1
fi

echo "  → 建置 Monitoring overlay..."
if kustomize build cluster/overlays/monitoring > /tmp/kustomize-monitoring.yaml 2>&1; then
    echo "  ✅ Monitoring 建置成功"
    echo "     資源數量: $(grep -c '^---' /tmp/kustomize-monitoring.yaml || echo "1")"
else
    echo "  ❌ Monitoring 建置失敗"
    kustomize build cluster/overlays/monitoring
    exit 1
fi
echo ""

# 檢查映像參考
echo "[4/4] 檢查容器映像參考..."
grep -r "image:" apps/ cluster/ | grep -v "^#" | grep -v "kustomization" | while read -r line; do
    echo "  $line"
done
echo "✅ 映像參考檢查完成"
echo ""

echo "========================================="
echo "✅ 所有驗證通過！"
echo "========================================="
echo ""
echo "生成的清單檔案："
echo "  - /tmp/kustomize-prod.yaml (Production)"
echo "  - /tmp/kustomize-monitoring.yaml (Monitoring)"
echo ""
echo "下一步："
echo "1. 如果還沒有 GKE 叢集，執行: bash scripts/oneclick_gke_init.sh"
echo "2. 部署到叢集: kubectl apply -k cluster/overlays/prod"
echo "3. 部署監控: kubectl apply -k cluster/overlays/monitoring"
echo "4. 查看狀態: kubectl get all -n flowagent"
echo ""
