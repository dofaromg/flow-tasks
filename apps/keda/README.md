# KEDA 安裝說明
# 
# KEDA (Kubernetes Event Driven Autoscaling) 允許基於事件驅動的自動擴展
#
# 安裝 KEDA：
# kubectl apply -f https://github.com/kedacore/keda/releases/latest/download/keda-2.13.1.yaml
#
# 驗證安裝：
# kubectl get pods -n keda
#
# 本目錄包含 KEDA ScaledObject 配置，用於自動擴展應用程式
