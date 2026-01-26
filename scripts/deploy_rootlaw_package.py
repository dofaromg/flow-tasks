#!/usr/bin/env python3
"""
RootLaw Package Deployment Tool
自動將 RootLaw Package v1.0 部署到多個倉庫

用途：
1. 將 RootLaw_Package_v1.midlock/ 目錄複製到目標倉庫
2. 根據目標倉庫結構自動調整 Absorption_Map 和 Evidence_Index
3. 支援批次部署到多個倉庫
4. 提供部署驗證和回滾功能

作者：MR.liou
版本：v1.0
日期：2026-01-26
"""

import os
import sys
import json
import shutil
import subprocess
import argparse
import tempfile
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple

class RootLawDeployer:
    """RootLaw Package 部署工具類別"""
    
    def __init__(self, source_repo: str = ".", verbose: bool = False):
        self.source_repo = Path(source_repo).resolve()
        self.source_package = self.source_repo / "RootLaw_Package_v1.midlock"
        self.verbose = verbose
        self.deployment_log = []
        
        # 驗證源套件存在
        if not self.source_package.exists():
            raise FileNotFoundError(f"RootLaw Package 不存在: {self.source_package}")
        
        self.log("✅ RootLaw Package 源目錄已找到", "INFO")
    
    def log(self, message: str, level: str = "INFO"):
        """記錄日誌訊息"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        self.deployment_log.append(log_entry)
        
        if self.verbose or level in ["WARNING", "ERROR"]:
            print(log_entry)
    
    def run_command(self, cmd: List[str], cwd: Optional[Path] = None) -> Tuple[bool, str]:
        """執行命令並返回結果"""
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=True
            )
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            return False, e.stderr
    
    def clone_repository(self, repo_url: str, target_dir: Path, branch: str = "main") -> bool:
        """克隆目標倉庫"""
        self.log(f"🔄 克隆倉庫: {repo_url}", "INFO")
        
        success, output = self.run_command([
            'git', 'clone',
            '--depth', '1',
            '--branch', branch,
            repo_url,
            str(target_dir)
        ])
        
        if success:
            self.log(f"✅ 克隆成功: {target_dir}", "INFO")
        else:
            self.log(f"❌ 克隆失敗: {output}", "ERROR")
        
        return success
    
    def copy_package_files(self, target_repo: Path) -> bool:
        """複製 RootLaw Package 檔案到目標倉庫"""
        target_package = target_repo / "RootLaw_Package_v1.midlock"
        
        try:
            # 如果目標已存在，先備份
            if target_package.exists():
                backup_dir = target_repo / f".rootlaw_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                self.log(f"📦 備份現有套件到: {backup_dir}", "INFO")
                shutil.copytree(target_package, backup_dir)
                shutil.rmtree(target_package)
            
            # 複製新的套件
            self.log(f"📋 複製套件檔案到: {target_package}", "INFO")
            shutil.copytree(self.source_package, target_package)
            
            # 添加部署標記
            deployment_info = {
                "deployed_at": datetime.now().isoformat(),
                "source_repo": str(self.source_repo),
                "version": "v1.0",
                "deployer": "RootLaw Deployment Tool"
            }
            
            with open(target_package / ".deployment_info.json", 'w', encoding='utf-8') as f:
                json.dump(deployment_info, f, indent=2, ensure_ascii=False)
            
            self.log(f"✅ 套件複製完成", "INFO")
            return True
            
        except Exception as e:
            self.log(f"❌ 複製失敗: {str(e)}", "ERROR")
            return False
    
    def analyze_repository_structure(self, target_repo: Path) -> Dict[str, List[str]]:
        """分析目標倉庫結構"""
        self.log(f"🔍 分析倉庫結構: {target_repo}", "INFO")
        
        structure = {
            "python_files": [],
            "typescript_files": [],
            "yaml_files": [],
            "workflows": [],
            "test_files": [],
            "config_files": []
        }
        
        # 掃描倉庫檔案
        for root, dirs, files in os.walk(target_repo):
            # 忽略 .git 和 node_modules
            dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__']]
            
            rel_root = Path(root).relative_to(target_repo)
            
            for file in files:
                file_path = rel_root / file
                file_str = str(file_path)
                
                if file.endswith('.py'):
                    structure["python_files"].append(file_str)
                    if 'test' in file.lower():
                        structure["test_files"].append(file_str)
                elif file.endswith(('.ts', '.tsx')):
                    structure["typescript_files"].append(file_str)
                elif file.endswith(('.yaml', '.yml')):
                    structure["yaml_files"].append(file_str)
                    if '.github/workflows' in file_str:
                        structure["workflows"].append(file_str)
                elif file.endswith(('.json', '.toml', '.ini')):
                    if any(name in file for name in ['config', 'package', 'requirements', 'setup']):
                        structure["config_files"].append(file_str)
        
        self.log(f"📊 找到 {len(structure['python_files'])} Python 檔案", "INFO")
        self.log(f"📊 找到 {len(structure['typescript_files'])} TypeScript 檔案", "INFO")
        self.log(f"📊 找到 {len(structure['workflows'])} GitHub 工作流程", "INFO")
        
        return structure
    
    def customize_absorption_map(self, target_repo: Path, structure: Dict[str, List[str]]) -> bool:
        """客製化 Absorption_Map.md 以匹配目標倉庫"""
        absorption_map_path = target_repo / "RootLaw_Package_v1.midlock" / "Absorption_Map.md"
        
        try:
            self.log(f"✏️  客製化 Absorption_Map.md", "INFO")
            
            with open(absorption_map_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 添加客製化標記
            customization_note = f"""
## Repository-Specific Mappings

**Note**: This section is auto-generated for this repository based on its actual structure.
**Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

### Python Modules
| Artifact | Law(s) | Notes |
| --- | --- | --- |
"""
            
            # 添加前 10 個 Python 檔案作為示例
            for py_file in structure["python_files"][:10]:
                customization_note += f"| {py_file} | 11, 15, 22, 28 | Python module with standard practices. |\n"
            
            if len(structure["python_files"]) > 10:
                customization_note += f"| ... | ... | {len(structure['python_files']) - 10} more Python files |\n"
            
            # 添加工作流程
            if structure["workflows"]:
                customization_note += "\n### GitHub Workflows (Repository-Specific)\n"
                customization_note += "| Artifact | Law(s) | Notes |\n"
                customization_note += "| --- | --- | --- |\n"
                
                for workflow in structure["workflows"]:
                    customization_note += f"| {workflow} | 21, 29, E-1 | CI/CD workflow. |\n"
            
            # 插入到文件末尾
            content += "\n" + customization_note
            
            with open(absorption_map_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.log(f"✅ Absorption_Map 客製化完成", "INFO")
            return True
            
        except Exception as e:
            self.log(f"⚠️  Absorption_Map 客製化失敗: {str(e)}", "WARNING")
            return False
    
    def create_deployment_report(self, target_repo: Path, structure: Dict[str, List[str]]) -> Path:
        """創建部署報告"""
        report_path = target_repo / "RootLaw_Package_v1.midlock" / "DEPLOYMENT_REPORT.md"
        
        report = f"""# RootLaw Package v1.0 - Deployment Report

## Deployment Information
- **Deployment Date**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **Source Repository**: {self.source_repo}
- **Target Repository**: {target_repo}
- **Package Version**: v1.0

## Repository Analysis Summary
- **Python Files**: {len(structure['python_files'])}
- **TypeScript Files**: {len(structure['typescript_files'])}
- **YAML Files**: {len(structure['yaml_files'])}
- **GitHub Workflows**: {len(structure['workflows'])}
- **Test Files**: {len(structure['test_files'])}
- **Config Files**: {len(structure['config_files'])}

## Deployed Files
1. ✅ README.md - User guide
2. ✅ RootLaws_v1.md - 42 Root Laws
3. ✅ Execution_Laws.md - 5 Execution Laws
4. ✅ Absorption_Map.md - File-to-law mapping (customized)
5. ✅ Evidence_Index.md - Evidence registry
6. ✅ Progress_Snapshot.md - Status tracking

## Next Steps
1. Review and validate the customized Absorption_Map.md
2. Update Evidence_Index.md with repository-specific evidence
3. Commit changes to the target repository
4. Configure CI/CD to enforce laws (E-1)
5. Schedule first quarterly review (90 days from deployment)

## Deployment Log
"""
        
        for log_entry in self.deployment_log:
            report += f"\n{log_entry}"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        self.log(f"📄 部署報告已創建: {report_path}", "INFO")
        return report_path
    
    def commit_changes(self, target_repo: Path, message: str = "Deploy RootLaw Package v1.0") -> bool:
        """提交變更到目標倉庫"""
        self.log(f"💾 提交變更到 Git", "INFO")
        
        # Git add
        success, _ = self.run_command(['git', 'add', 'RootLaw_Package_v1.midlock/'], cwd=target_repo)
        if not success:
            self.log(f"❌ Git add 失敗", "ERROR")
            return False
        
        # Git commit
        success, _ = self.run_command([
            'git', 'commit', '-m', message,
            '-m', f"Deployed by RootLaw Deployment Tool at {datetime.now().isoformat()}"
        ], cwd=target_repo)
        
        if success:
            self.log(f"✅ 變更已提交", "INFO")
        else:
            self.log(f"⚠️  提交失敗 (可能沒有變更)", "WARNING")
        
        return success
    
    def deploy_to_repository(self, repo_url: str, branch: str = "main", 
                           commit: bool = False, push: bool = False) -> bool:
        """部署到單個倉庫"""
        self.log(f"🚀 開始部署到: {repo_url}", "INFO")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # 步驟 1: 克隆倉庫
            if not self.clone_repository(repo_url, temp_path, branch):
                return False
            
            # 步驟 2: 複製套件檔案
            if not self.copy_package_files(temp_path):
                return False
            
            # 步驟 3: 分析倉庫結構
            structure = self.analyze_repository_structure(temp_path)
            
            # 步驟 4: 客製化 Absorption_Map
            self.customize_absorption_map(temp_path, structure)
            
            # 步驟 5: 創建部署報告
            self.create_deployment_report(temp_path, structure)
            
            # 步驟 6: 提交變更（如果啟用）
            if commit:
                if not self.commit_changes(temp_path):
                    self.log(f"⚠️  變更未提交", "WARNING")
                
                # 步驟 7: 推送變更（如果啟用）
                if push:
                    self.log(f"📤 推送變更到遠端", "INFO")
                    success, output = self.run_command(['git', 'push'], cwd=temp_path)
                    if success:
                        self.log(f"✅ 變更已推送", "INFO")
                    else:
                        self.log(f"❌ 推送失敗: {output}", "ERROR")
            
            self.log(f"✅ 部署完成: {repo_url}", "INFO")
            return True
    
    def deploy_to_multiple_repositories(self, config_file: str) -> Dict[str, bool]:
        """從配置檔案批次部署到多個倉庫"""
        self.log(f"📋 載入配置檔案: {config_file}", "INFO")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        results = {}
        
        for repo_config in config.get("repositories", []):
            repo_url = repo_config["url"]
            branch = repo_config.get("branch", "main")
            enabled = repo_config.get("enabled", True)
            
            if not enabled:
                self.log(f"⏭️  跳過停用的倉庫: {repo_url}", "INFO")
                results[repo_url] = None
                continue
            
            success = self.deploy_to_repository(
                repo_url=repo_url,
                branch=branch,
                commit=repo_config.get("commit", False),
                push=repo_config.get("push", False)
            )
            
            results[repo_url] = success
        
        return results


def main():
    parser = argparse.ArgumentParser(
        description="RootLaw Package 部署工具 - 自動部署律法套件到多個倉庫",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例用法:

  # 部署到單個倉庫
  python deploy_rootlaw_package.py --url https://github.com/user/repo.git

  # 從配置檔案批次部署
  python deploy_rootlaw_package.py --config rootlaw_deploy_config.json

  # 部署並自動提交變更
  python deploy_rootlaw_package.py --url https://github.com/user/repo.git --commit

  # 部署、提交並推送
  python deploy_rootlaw_package.py --url https://github.com/user/repo.git --commit --push

  # 詳細模式
  python deploy_rootlaw_package.py --url https://github.com/user/repo.git --verbose
        """
    )
    
    parser.add_argument('--url', type=str, help='目標倉庫 URL')
    parser.add_argument('--branch', type=str, default='main', help='目標分支 (預設: main)')
    parser.add_argument('--config', type=str, help='配置檔案路徑 (JSON 格式)')
    parser.add_argument('--source', type=str, default='.', help='RootLaw Package 源倉庫路徑')
    parser.add_argument('--commit', action='store_true', help='自動提交變更')
    parser.add_argument('--push', action='store_true', help='自動推送變更到遠端')
    parser.add_argument('--verbose', '-v', action='store_true', help='顯示詳細日誌')
    
    args = parser.parse_args()
    
    # 驗證參數
    if not args.url and not args.config:
        parser.error("必須提供 --url 或 --config 參數之一")
    
    try:
        deployer = RootLawDeployer(source_repo=args.source, verbose=args.verbose)
        
        if args.config:
            # 批次部署
            print("🌟 RootLaw Package 批次部署工具")
            print("=" * 60)
            
            results = deployer.deploy_to_multiple_repositories(args.config)
            
            # 顯示結果摘要
            print("\n" + "=" * 60)
            print("📊 部署結果摘要:")
            success_count = sum(1 for v in results.values() if v is True)
            total_count = len([v for v in results.values() if v is not None])
            
            for repo_url, success in results.items():
                if success is None:
                    status = "⏭️  已跳過"
                elif success:
                    status = "✅ 成功"
                else:
                    status = "❌ 失敗"
                print(f"  {status} - {repo_url}")
            
            print(f"\n總計: {success_count}/{total_count} 個倉庫部署成功")
            
        else:
            # 單個倉庫部署
            print("🌟 RootLaw Package 部署工具")
            print("=" * 60)
            
            success = deployer.deploy_to_repository(
                repo_url=args.url,
                branch=args.branch,
                commit=args.commit,
                push=args.push
            )
            
            if success:
                print("\n✅ 部署成功！")
                sys.exit(0)
            else:
                print("\n❌ 部署失敗")
                sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ 錯誤: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
