# MongoDB 密碼管理指南 / MongoDB Password Management Guide

**版本 / Version**: 1.0.0  
**更新日期 / Updated**: 2026-02-10

---

## 🔒 安全概覽 / Security Overview

此專案已實施安全的密碼管理策略，**不再在 Git 倉庫中存儲明文密碼**。

This project has implemented secure password management and **no longer stores plaintext passwords in the Git repository**.

### 改進內容 / Improvements

- ✅ **移除硬編碼密碼** / Removed hardcoded passwords
- ✅ **使用 Kubernetes Secrets** / Using Kubernetes Secrets
- ✅ **支援環境變數配置** / Environment variable configuration support
- ✅ **自動密碼生成工具** / Automated password generation tool
- ✅ **完整的文檔說明** / Comprehensive documentation

---

## 🚀 快速開始 / Quick Start

### 方法 1: 自動生成密碼（推薦）/ Method 1: Auto-generate Password (Recommended)

```bash
# 生成並顯示新密碼 / Generate and display new password
bash scripts/generate_password.sh

# 生成並自動配置到本地 / Generate and auto-configure locally
bash scripts/generate_password.sh --apply
```

### 方法 2: 手動配置 / Method 2: Manual Configuration

```bash
# 1. 複製環境變數範例檔案 / Copy environment variables example
cp .env.example .env

# 2. 生成安全密碼 / Generate secure password
openssl rand -base64 32

# 3. 編輯 .env 並設置密碼 / Edit .env and set password
nano .env
# 將 YOUR_SECURE_PASSWORD_HERE 替換為生成的密碼
```

---

## 📋 部署場景 / Deployment Scenarios

### 場景 1: 本地開發（Docker Compose）/ Scenario 1: Local Development (Docker Compose)

```bash
# 1. 配置密碼 / Configure password
bash scripts/generate_password.sh --apply

# 2. 啟動服務 / Start services
docker-compose --env-file .env up -d

# 3. 驗證連接 / Verify connection
docker-compose exec mongodb mongosh -u admin -p $(grep MONGODB_PASSWORD .env | cut -d'=' -f2)
```

### 場景 2: Kubernetes 部署 / Scenario 2: Kubernetes Deployment

#### 步驟 1: 生成密碼 / Step 1: Generate Password

```bash
# 生成新密碼 / Generate new password
NEW_PASSWORD=$(openssl rand -base64 32)
echo "新密碼 / New password: $NEW_PASSWORD"
```

#### 步驟 2: 創建 Secret / Step 2: Create Secret

```bash
# 創建 MongoDB Secret
kubectl create secret generic mongodb-secret \
  --from-literal=password="$NEW_PASSWORD" \
  --namespace=flowagent
```

或使用 dry-run 預覽：

```bash
# 預覽 Secret 配置（不會實際創建）
kubectl create secret generic mongodb-secret \
  --from-literal=password="$NEW_PASSWORD" \
  --namespace=flowagent \
  --dry-run=client -o yaml
```

#### 步驟 3: 部署應用 / Step 3: Deploy Applications

```bash
# 部署所有服務 / Deploy all services
kubectl apply -k cluster/overlays/prod/

# 驗證部署 / Verify deployment
kubectl get pods -n flowagent
kubectl get secret mongodb-secret -n flowagent
```

#### 步驟 4: 驗證密碼 / Step 4: Verify Password

```bash
# 查看 Secret 中的密碼 / View password in Secret
kubectl get secret mongodb-secret -n flowagent -o jsonpath='{.data.password}' | base64 -d
```

### 場景 3: Google Secret Manager（生產環境推薦）/ Scenario 3: Google Secret Manager (Production Recommended)

#### 步驟 1: 創建 Secret / Step 1: Create Secret in Secret Manager

```bash
# 生成並存儲到 Secret Manager
NEW_PASSWORD=$(openssl rand -base64 32)
echo "$NEW_PASSWORD" | gcloud secrets create mongodb-password \
  --data-file=- \
  --project=flowmemorysync \
  --replication-policy=automatic
```

#### 步驟 2: 授權訪問 / Step 2: Grant Access

```bash
# 允許 GKE 服務帳號訪問 Secret
gcloud secrets add-iam-policy-binding mongodb-password \
  --member="serviceAccount:flowagent@flowmemorysync.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

#### 步驟 3: 使用 External Secrets Operator / Step 3: Use External Secrets Operator

安裝 External Secrets Operator:

```bash
# 安裝 Helm
helm repo add external-secrets https://charts.external-secrets.io
helm repo update

# 安裝 External Secrets Operator
helm install external-secrets \
  external-secrets/external-secrets \
  -n external-secrets-system \
  --create-namespace
```

創建 ExternalSecret 資源：

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: mongodb-external-secret
  namespace: flowagent
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: gcpsm-secret-store
    kind: SecretStore
  target:
    name: mongodb-secret
    creationPolicy: Owner
  data:
  - secretKey: password
    remoteRef:
      key: mongodb-password
```

---

## 🔧 密碼配置檔案 / Password Configuration Files

### 已更新的檔案 / Updated Files

| 檔案 / File | 變更 / Changes |
|-------------|---------------|
| `apps/mongodb/secret.yaml` | 移除硬編碼密碼，添加配置說明 / Removed hardcoded password, added instructions |
| `apps/orchestrator/deployment.yaml` | 使用 Secret 引用密碼 / Using Secret reference for password |
| `apps/module-a/deployment.yaml` | 使用 Secret 引用密碼 / Using Secret reference for password |
| `docker-compose.yml` | 使用環境變數 `${MONGODB_PASSWORD}` / Using environment variable |
| `.env.example` | 完整的環境變數範例 / Complete environment variable template |

### Kubernetes Secret 引用方式 / Kubernetes Secret Reference

在 Deployment 中引用 Secret：

```yaml
env:
- name: MONGODB_PASSWORD
  valueFrom:
    secretKeyRef:
      name: mongodb-secret
      key: password
- name: MONGODB_URI
  value: "mongodb://admin:$(MONGODB_PASSWORD)@mongodb:27017"
```

---

## 🛠️ 工具使用說明 / Tool Usage Guide

### 密碼生成腳本 / Password Generation Script

**位置 / Location**: `scripts/generate_password.sh`

**功能 / Features**:
- ✅ 生成 32 字節安全隨機密碼 / Generate 32-byte secure random password
- ✅ 自動創建 `.env` 檔案 / Automatically create `.env` file
- ✅ 提供 Kubernetes 部署命令 / Provide Kubernetes deployment commands
- ✅ 彩色控制台輸出 / Colored console output
- ✅ 安全提醒 / Security reminders

**使用方法 / Usage**:

```bash
# 僅生成密碼並顯示 / Generate password and display only
bash scripts/generate_password.sh

# 生成密碼並應用到本地配置 / Generate and apply to local config
bash scripts/generate_password.sh --apply
```

**輸出示例 / Output Example**:

```
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║        MongoDB 密碼生成工具 / Password Generator              ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝

[INFO] 已生成新的 MongoDB 密碼 / New MongoDB password generated

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
新密碼 / New Password:

  eleUzgDNFQCaOfwYzJLtbawhBbzStn9w3ZprMkPu0cM=

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 🔐 安全最佳實踐 / Security Best Practices

### ✅ 必須執行 / Must Do

1. **立即更換預設密碼** / Immediately change default passwords
   ```bash
   bash scripts/generate_password.sh --apply
   ```

2. **使用強隨機密碼** / Use strong random passwords
   - 至少 32 字元 / At least 32 characters
   - 包含大小寫字母、數字和符號 / Include uppercase, lowercase, numbers, and symbols
   - 使用密碼生成工具 / Use password generation tools

3. **保護 .env 檔案** / Protect .env file
   ```bash
   # 設置適當的檔案權限 / Set appropriate file permissions
   chmod 600 .env
   ```

4. **不要提交密碼到 Git** / Do not commit passwords to Git
   - `.env` 已在 `.gitignore` 中 / `.env` is in `.gitignore`
   - 定期檢查 `git status` / Regularly check `git status`

### ✅ 強烈建議 / Strongly Recommended

1. **使用 Secret Manager** / Use Secret Manager
   - Google Secret Manager (GCP)
   - AWS Secrets Manager
   - Azure Key Vault
   - HashiCorp Vault

2. **定期輪換密碼** / Regularly rotate passwords
   - 建議每 90 天更換一次 / Recommended every 90 days
   - 記錄在安全的密碼管理器中 / Record in secure password manager

3. **限制訪問權限** / Limit access permissions
   - 最小權限原則 / Principle of least privilege
   - 使用 RBAC 控制 Secret 訪問 / Use RBAC to control Secret access

4. **啟用審計日誌** / Enable audit logging
   ```bash
   # 查看 Secret 訪問日誌 / View Secret access logs
   kubectl get events -n flowagent | grep mongodb-secret
   ```

### ⚠️ 禁止事項 / Prohibited Actions

- ❌ 不要在代碼中硬編碼密碼 / Do not hardcode passwords in code
- ❌ 不要在日誌中輸出密碼 / Do not output passwords in logs
- ❌ 不要通過聊天或郵件發送密碼 / Do not send passwords via chat or email
- ❌ 不要使用弱密碼或常見密碼 / Do not use weak or common passwords
- ❌ 不要在多個系統使用相同密碼 / Do not use the same password across systems

---

## 📊 密碼輪換流程 / Password Rotation Process

### Kubernetes 環境 / Kubernetes Environment

```bash
# 1. 生成新密碼 / Generate new password
NEW_PASSWORD=$(openssl rand -base64 32)

# 2. 更新 Secret / Update Secret
kubectl create secret generic mongodb-secret \
  --from-literal=password="$NEW_PASSWORD" \
  --namespace=flowagent \
  --dry-run=client -o yaml | kubectl apply -f -

# 3. 重啟相關 Pods（觸發密碼更新）/ Restart related Pods
kubectl rollout restart deployment/mongodb -n flowagent
kubectl rollout restart deployment/module-a -n flowagent
kubectl rollout restart deployment/orchestrator -n flowagent

# 4. 驗證部署 / Verify deployment
kubectl get pods -n flowagent
```

### Docker Compose 環境 / Docker Compose Environment

```bash
# 1. 生成並更新 .env / Generate and update .env
bash scripts/generate_password.sh --apply

# 2. 重啟服務 / Restart services
docker-compose down
docker-compose --env-file .env up -d

# 3. 驗證連接 / Verify connection
docker-compose ps
```

---

## 🆘 故障排除 / Troubleshooting

### 問題 1: Pod 無法連接到 MongoDB / Issue 1: Pods cannot connect to MongoDB

**症狀 / Symptoms**:
```
Error: Authentication failed
```

**解決方案 / Solution**:

```bash
# 1. 檢查 Secret 是否存在 / Check if Secret exists
kubectl get secret mongodb-secret -n flowagent

# 2. 驗證 Secret 內容 / Verify Secret content
kubectl get secret mongodb-secret -n flowagent -o yaml

# 3. 確認 Pod 環境變數 / Check Pod environment variables
kubectl exec -it deployment/module-a -n flowagent -- env | grep MONGODB

# 4. 查看 Pod 日誌 / View Pod logs
kubectl logs deployment/module-a -n flowagent
```

### 問題 2: Docker Compose 密碼無效 / Issue 2: Docker Compose password invalid

**症狀 / Symptoms**:
```
Authentication failed
```

**解決方案 / Solution**:

```bash
# 1. 檢查 .env 檔案 / Check .env file
cat .env | grep MONGODB_PASSWORD

# 2. 確認環境變數載入 / Verify environment variable loading
docker-compose config | grep MONGO_INITDB_ROOT_PASSWORD

# 3. 刪除舊的卷並重新創建 / Remove old volumes and recreate
docker-compose down -v
docker-compose --env-file .env up -d
```

### 問題 3: 密碼包含特殊字元導致問題 / Issue 3: Special characters in password cause issues

**解決方案 / Solution**:

```bash
# 使用 base64 編碼的密碼（不包含特殊字元）
# Use base64 encoded password (no special characters)
openssl rand -base64 32

# 或在 YAML 中使用引號包裹
# Or wrap in quotes in YAML
password: "your-password-with-special-chars"
```

---

## 📞 支援與資源 / Support & Resources

### 相關文檔 / Related Documentation

- 📊 [專業部署分析報告](./專業部署分析報告.md)
- 📋 [部署執行摘要](./部署執行摘要.md)
- 🎯 [實際部署指南](./實際部署指南.md)
- 🔧 [Docker Compose 指南](./DOCKER_COMPOSE_GUIDE.md)

### 外部資源 / External Resources

- 🔗 [Kubernetes Secrets](https://kubernetes.io/docs/concepts/configuration/secret/)
- 🔗 [Google Secret Manager](https://cloud.google.com/secret-manager)
- 🔗 [External Secrets Operator](https://external-secrets.io/)
- 🔗 [OWASP Password Storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)

### 緊急聯絡 / Emergency Contact

- GitHub Issues: https://github.com/dofaromg/flow-tasks/issues
- 安全問題 / Security Issues: 使用 GitHub Security Advisory

---

## 📝 變更歷史 / Change History

| 版本 / Version | 日期 / Date | 變更內容 / Changes |
|---------------|------------|-------------------|
| 1.0.0 | 2026-02-10 | 初始版本 - 實施安全密碼管理 / Initial version - Secure password management |

---

**文檔版本 / Document Version**: 1.0.0  
**最後更新 / Last Updated**: 2026-02-10  
**作者 / Author**: GitHub Copilot - Security Specialist

© 2026 FlowAgent Project. 保留所有權利 / All rights reserved.
