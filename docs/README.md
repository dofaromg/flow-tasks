# Documentation Organization

This directory contains organized documentation for the FlowAgent project.

## Structure

### 📚 Active Documentation (Root Directory)
Key documents that are actively maintained and referenced:
- `ARCHITECTURE.md` - System architecture overview
- `DEPLOYMENT.md` - Deployment guide
- `README.md` - Project overview
- `QUICKSTART.md` - Quick start guide
- `CODESPACE_MANAGEMENT.md` - Codespace lifecycle management
- `BRANCH_INTEGRATION_GUIDE.md` - Branch integration best practices

### 🎯 Consolidated Guides (`docs/`)
- `performance/PERFORMANCE_GUIDE.md` - Consolidated performance optimization guide
- `implementation/IMPLEMENTATION_GUIDE.md` - Consolidated implementation documentation
- `COPILOT_PERMISSION_GUIDE.md` - GitHub Copilot 權限升級指南 / Permission upgrade guide

### ⚙️ Configuration Files (`config/`)
- `config.sample.yaml` - 生產環境配置範本 / Production config template
- `dev-mode.yaml` - 開發模式配置（無限制）/ Dev mode config (unrestricted)

### 📦 Archive (`docs/archive/`)
Historical documents and superseded files:
- Old performance documents (7 files consolidated)
- Old implementation documents (3 files consolidated)
- Files with "下載" (download), "複製" (copy), "重新" (re-) prefixes
- Superseded conversation extractor docs
- Additional suggestions and summaries

## File Organization Guidelines

### Active Documents
Keep in root if:
- Frequently referenced
- Part of core documentation
- Actively maintained

### Should be Archived
Move to `docs/archive/` if:
- Superseded by newer documentation
- Historical reference only
- Duplicate or temporary files
- Implementation-specific temporary docs

## Migration Notes

Consolidated on 2026-01-14:
- 7 PERFORMANCE_*.md files → `performance/PERFORMANCE_GUIDE.md`
- 3 IMPLEMENTATION_*.md files → `implementation/IMPLEMENTATION_GUIDE.md`
- Moved 15+ scattered files to archive

## Finding Archived Content

All archived files maintain their original names for easy reference. Use:
```bash
find docs/archive/ -name "PERFORMANCE*"
find docs/archive/ -name "IMPLEMENTATION*"
```
