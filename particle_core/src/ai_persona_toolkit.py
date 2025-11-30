#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRLiou AI 模組人格通用套件 (AI Persona Universal Toolkit)
提供 AI 人格連結器、ZIP 壓縮/解壓縮功能（無檔案名稱限制）

功能特色:
- 人格連結器: 連接、管理與切換多個 AI 人格模組
- 通用壓縮器: 支援任意檔案名稱的 ZIP 壓縮/解壓縮
- 模組化設計: 可擴展的人格與功能模組系統
"""

import json
import os
import zipfile
import hashlib
import shutil
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Callable
from pathlib import Path
from io import BytesIO
import base64


class PersonaConnector:
    """
    AI 人格連結器
    用於連接、管理與切換多個 AI 人格模組
    """
    
    def __init__(self, registry_path: Optional[str] = None):
        """
        初始化人格連結器
        
        Args:
            registry_path: 人格註冊表路徑（JSON 格式）
        """
        self.personas: Dict[str, Dict[str, Any]] = {}
        self.active_persona: Optional[str] = None
        self.connections: Dict[str, Dict[str, Any]] = {}
        self.hooks: Dict[str, List[Callable]] = {
            "on_connect": [],
            "on_disconnect": [],
            "on_switch": [],
            "on_message": []
        }
        
        if registry_path and os.path.exists(registry_path):
            self.load_registry(registry_path)
    
    def register_persona(
        self,
        persona_id: str,
        name: str,
        role: Union[str, List[str]],
        traits: Optional[List[str]] = None,
        modules: Optional[List[str]] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        註冊新的 AI 人格
        
        Args:
            persona_id: 人格唯一識別碼
            name: 人格名稱
            role: 角色（可以是字串或列表）
            traits: 特質列表
            modules: 關聯模組列表
            config: 額外配置
            
        Returns:
            註冊結果
        """
        persona = {
            "id": persona_id,
            "name": name,
            "role": [role] if isinstance(role, str) else role,
            "traits": traits or [],
            "modules": modules or [],
            "config": config or {},
            "registered_at": datetime.now().isoformat(),
            "status": "inactive"
        }
        
        self.personas[persona_id] = persona
        
        return {
            "success": True,
            "persona_id": persona_id,
            "message": f"人格 '{name}' 已成功註冊"
        }
    
    def connect(self, persona_id: str, connection_config: Optional[Dict] = None) -> Dict[str, Any]:
        """
        連接到指定的 AI 人格
        
        Args:
            persona_id: 人格識別碼
            connection_config: 連接配置
            
        Returns:
            連接結果
        """
        if persona_id not in self.personas:
            return {
                "success": False,
                "error": f"人格 '{persona_id}' 不存在"
            }
        
        connection = {
            "persona_id": persona_id,
            "connected_at": datetime.now().isoformat(),
            "config": connection_config or {},
            "status": "connected"
        }
        
        self.connections[persona_id] = connection
        self.personas[persona_id]["status"] = "active"
        
        # 觸發連接鉤子
        self._trigger_hooks("on_connect", persona_id, connection)
        
        return {
            "success": True,
            "persona_id": persona_id,
            "connection": connection,
            "message": f"已成功連接到人格 '{self.personas[persona_id]['name']}'"
        }
    
    def disconnect(self, persona_id: str) -> Dict[str, Any]:
        """
        斷開與指定人格的連接
        
        Args:
            persona_id: 人格識別碼
            
        Returns:
            斷開結果
        """
        if persona_id not in self.connections:
            return {
                "success": False,
                "error": f"人格 '{persona_id}' 未連接"
            }
        
        # 觸發斷開鉤子
        self._trigger_hooks("on_disconnect", persona_id, self.connections[persona_id])
        
        del self.connections[persona_id]
        if persona_id in self.personas:
            self.personas[persona_id]["status"] = "inactive"
        
        if self.active_persona == persona_id:
            self.active_persona = None
        
        return {
            "success": True,
            "persona_id": persona_id,
            "message": f"已斷開與人格 '{persona_id}' 的連接"
        }
    
    def switch_persona(self, persona_id: str) -> Dict[str, Any]:
        """
        切換到指定的活動人格
        
        Args:
            persona_id: 人格識別碼
            
        Returns:
            切換結果
        """
        if persona_id not in self.connections:
            # 嘗試自動連接
            connect_result = self.connect(persona_id)
            if not connect_result["success"]:
                return connect_result
        
        old_persona = self.active_persona
        self.active_persona = persona_id
        
        # 觸發切換鉤子
        self._trigger_hooks("on_switch", old_persona, persona_id)
        
        return {
            "success": True,
            "previous_persona": old_persona,
            "current_persona": persona_id,
            "message": f"已切換到人格 '{self.personas[persona_id]['name']}'"
        }
    
    def get_active_persona(self) -> Optional[Dict[str, Any]]:
        """
        獲取當前活動人格
        
        Returns:
            活動人格資訊或 None
        """
        if self.active_persona and self.active_persona in self.personas:
            return self.personas[self.active_persona]
        return None
    
    def list_personas(self, filter_status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        列出所有人格
        
        Args:
            filter_status: 過濾狀態（'active', 'inactive'）
            
        Returns:
            人格列表
        """
        personas = list(self.personas.values())
        
        if filter_status:
            personas = [p for p in personas if p["status"] == filter_status]
        
        return personas
    
    def send_message(self, message: str, persona_id: Optional[str] = None) -> Dict[str, Any]:
        """
        向人格發送訊息
        
        Args:
            message: 訊息內容
            persona_id: 目標人格（若為 None 則使用活動人格）
            
        Returns:
            發送結果
        """
        target_id = persona_id or self.active_persona
        
        if not target_id:
            return {
                "success": False,
                "error": "沒有活動的人格，請先連接或切換到一個人格"
            }
        
        if target_id not in self.connections:
            return {
                "success": False,
                "error": f"人格 '{target_id}' 未連接"
            }
        
        # 觸發訊息鉤子
        self._trigger_hooks("on_message", target_id, message)
        
        return {
            "success": True,
            "persona_id": target_id,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
    
    def add_hook(self, event: str, callback: Callable) -> bool:
        """
        添加事件鉤子
        
        Args:
            event: 事件名稱
            callback: 回調函數
            
        Returns:
            是否成功添加
        """
        if event in self.hooks:
            self.hooks[event].append(callback)
            return True
        return False
    
    def load_registry(self, registry_path: str) -> Dict[str, Any]:
        """
        載入人格註冊表
        
        Args:
            registry_path: 註冊表路徑
            
        Returns:
            載入結果
        """
        with open(registry_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        loaded_count = 0
        if "personas" in data:
            for persona in data["personas"]:
                self.register_persona(
                    persona_id=persona.get("id", f"persona_{loaded_count}"),
                    name=persona.get("name", persona.get("id", "Unknown")),
                    role=persona.get("role", []),
                    traits=persona.get("traits", []),
                    modules=persona.get("modules", []),
                    config=persona.get("config", {})
                )
                loaded_count += 1
        
        return {
            "success": True,
            "loaded_count": loaded_count,
            "registry_path": registry_path
        }
    
    def save_registry(self, registry_path: str) -> str:
        """
        儲存人格註冊表
        
        Args:
            registry_path: 儲存路徑
            
        Returns:
            儲存的檔案路徑
        """
        data = {
            "personas": list(self.personas.values()),
            "saved_at": datetime.now().isoformat(),
            "version": "1.0"
        }
        
        with open(registry_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return registry_path
    
    def _trigger_hooks(self, event: str, *args) -> None:
        """觸發事件鉤子"""
        if event in self.hooks:
            for callback in self.hooks[event]:
                try:
                    callback(*args)
                except Exception as e:
                    print(f"Hook error ({event}): {e}")


class UniversalZipHandler:
    """
    通用 ZIP 壓縮/解壓縮處理器
    支援任意檔案名稱（無檔案名稱限制）
    """
    
    def __init__(self, temp_dir: Optional[str] = None):
        """
        初始化 ZIP 處理器
        
        Args:
            temp_dir: 暫存目錄路徑
        """
        self.temp_dir = Path(temp_dir) if temp_dir else Path("zip_temp")
        self.temp_dir.mkdir(exist_ok=True)
    
    def compress(
        self,
        source: Union[str, List[str], Dict[str, bytes]],
        output_path: Optional[str] = None,
        compression_level: int = zipfile.ZIP_DEFLATED,
        password: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        壓縮檔案或資料為 ZIP
        
        Args:
            source: 來源（檔案路徑、路徑列表、或 {檔名: 資料} 字典）
            output_path: 輸出 ZIP 路徑
            compression_level: 壓縮等級
            password: 密碼（選填，注意：標準 zipfile 不支援加密寫入）
            
        Returns:
            壓縮結果
        """
        if output_path is None:
            output_path = f"archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        
        files_added = []
        total_size = 0
        
        with zipfile.ZipFile(output_path, 'w', compression_level) as zf:
            if isinstance(source, dict):
                # 直接從記憶體資料壓縮
                for filename, data in source.items():
                    if isinstance(data, str):
                        data = data.encode('utf-8')
                    zf.writestr(filename, data)
                    files_added.append(filename)
                    total_size += len(data)
                    
            elif isinstance(source, list):
                # 壓縮多個檔案/目錄
                for path in source:
                    self._add_to_zip(zf, path, files_added)
                    
            elif isinstance(source, str):
                # 壓縮單個檔案或目錄
                self._add_to_zip(zf, source, files_added)
        
        # 計算壓縮後大小
        compressed_size = os.path.getsize(output_path)
        
        return {
            "success": True,
            "output_path": output_path,
            "files_count": len(files_added),
            "files": files_added,
            "original_size": total_size if isinstance(source, dict) else "N/A",
            "compressed_size": compressed_size,
            "checksum": self._calculate_checksum(output_path)
        }
    
    def decompress(
        self,
        zip_path: str,
        output_dir: Optional[str] = None,
        password: Optional[str] = None,
        extract_filter: Optional[Callable[[str], bool]] = None
    ) -> Dict[str, Any]:
        """
        解壓縮 ZIP 檔案
        
        Args:
            zip_path: ZIP 檔案路徑
            output_dir: 輸出目錄
            password: 密碼
            extract_filter: 過濾函數，決定哪些檔案要解壓
            
        Returns:
            解壓縮結果
        """
        if not os.path.exists(zip_path):
            return {
                "success": False,
                "error": f"ZIP 檔案不存在: {zip_path}"
            }
        
        if output_dir is None:
            output_dir = os.path.splitext(zip_path)[0] + "_extracted"
        
        os.makedirs(output_dir, exist_ok=True)
        
        files_extracted = []
        skipped_files = []
        
        pwd = password.encode() if password else None
        
        with zipfile.ZipFile(zip_path, 'r') as zf:
            for member in zf.namelist():
                # 應用過濾器
                if extract_filter and not extract_filter(member):
                    skipped_files.append(member)
                    continue
                
                # 安全性檢查：防止路徑穿越攻擊
                member_path = os.path.normpath(member)
                if member_path.startswith('..') or os.path.isabs(member_path):
                    skipped_files.append(member)
                    continue
                
                try:
                    zf.extract(member, output_dir, pwd=pwd)
                    files_extracted.append(member)
                except Exception as e:
                    skipped_files.append(f"{member} (錯誤: {e})")
        
        return {
            "success": True,
            "output_dir": output_dir,
            "files_count": len(files_extracted),
            "files": files_extracted,
            "skipped": skipped_files,
            "source": zip_path
        }
    
    def list_contents(self, zip_path: str) -> Dict[str, Any]:
        """
        列出 ZIP 檔案內容
        
        Args:
            zip_path: ZIP 檔案路徑
            
        Returns:
            內容列表
        """
        if not os.path.exists(zip_path):
            return {
                "success": False,
                "error": f"ZIP 檔案不存在: {zip_path}"
            }
        
        contents = []
        
        with zipfile.ZipFile(zip_path, 'r') as zf:
            for info in zf.infolist():
                contents.append({
                    "filename": info.filename,
                    "size": info.file_size,
                    "compressed_size": info.compress_size,
                    "is_dir": info.is_dir(),
                    "modified": datetime(*info.date_time).isoformat() if info.date_time else None
                })
        
        return {
            "success": True,
            "zip_path": zip_path,
            "count": len(contents),
            "contents": contents
        }
    
    def compress_to_memory(
        self,
        source: Union[str, List[str], Dict[str, bytes]]
    ) -> bytes:
        """
        壓縮為記憶體中的 ZIP 資料
        
        Args:
            source: 來源資料
            
        Returns:
            ZIP 資料（bytes）
        """
        buffer = BytesIO()
        
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            if isinstance(source, dict):
                for filename, data in source.items():
                    if isinstance(data, str):
                        data = data.encode('utf-8')
                    zf.writestr(filename, data)
            elif isinstance(source, list):
                for path in source:
                    self._add_to_zip(zf, path, [])
            elif isinstance(source, str):
                self._add_to_zip(zf, source, [])
        
        return buffer.getvalue()
    
    def decompress_from_memory(
        self,
        zip_data: bytes,
        output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        從記憶體中的 ZIP 資料解壓縮
        
        Args:
            zip_data: ZIP 資料（bytes）
            output_dir: 輸出目錄
            
        Returns:
            解壓縮結果
        """
        if output_dir is None:
            output_dir = str(self.temp_dir / f"extracted_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        os.makedirs(output_dir, exist_ok=True)
        
        buffer = BytesIO(zip_data)
        files_extracted = []
        
        with zipfile.ZipFile(buffer, 'r') as zf:
            for member in zf.namelist():
                # 安全性檢查
                member_path = os.path.normpath(member)
                if member_path.startswith('..') or os.path.isabs(member_path):
                    continue
                
                zf.extract(member, output_dir)
                files_extracted.append(member)
        
        return {
            "success": True,
            "output_dir": output_dir,
            "files_count": len(files_extracted),
            "files": files_extracted
        }
    
    def compress_to_base64(
        self,
        source: Union[str, List[str], Dict[str, bytes]]
    ) -> str:
        """
        壓縮並轉換為 Base64 字串
        
        Args:
            source: 來源資料
            
        Returns:
            Base64 編碼的 ZIP 資料
        """
        zip_data = self.compress_to_memory(source)
        return base64.b64encode(zip_data).decode('utf-8')
    
    def decompress_from_base64(
        self,
        base64_data: str,
        output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        從 Base64 字串解壓縮
        
        Args:
            base64_data: Base64 編碼的 ZIP 資料
            output_dir: 輸出目錄
            
        Returns:
            解壓縮結果
        """
        zip_data = base64.b64decode(base64_data)
        return self.decompress_from_memory(zip_data, output_dir)
    
    def _add_to_zip(self, zf: zipfile.ZipFile, path: str, files_added: List[str]) -> None:
        """將檔案或目錄加入 ZIP"""
        path = Path(path)
        
        if path.is_file():
            arcname = path.name
            zf.write(path, arcname)
            files_added.append(arcname)
            
        elif path.is_dir():
            for file_path in path.rglob('*'):
                if file_path.is_file():
                    arcname = str(file_path.relative_to(path.parent))
                    zf.write(file_path, arcname)
                    files_added.append(arcname)
    
    def _calculate_checksum(self, file_path: str) -> str:
        """計算檔案 SHA-256 校驗碼"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()


class AIPersonaToolkit:
    """
    AI 模組人格通用套件
    整合人格連結器與 ZIP 處理功能
    """
    
    def __init__(
        self,
        registry_path: Optional[str] = None,
        temp_dir: Optional[str] = None
    ):
        """
        初始化套件
        
        Args:
            registry_path: 人格註冊表路徑
            temp_dir: 暫存目錄
        """
        self.connector = PersonaConnector(registry_path)
        self.zip_handler = UniversalZipHandler(temp_dir)
        self.version = "1.0.0"
    
    def get_info(self) -> Dict[str, Any]:
        """
        獲取套件資訊
        
        Returns:
            套件資訊
        """
        return {
            "name": "MRLiou AI Persona Universal Toolkit",
            "name_zh": "MRLiou AI 模組人格通用套件",
            "version": self.version,
            "features": [
                "人格連結器 (PersonaConnector)",
                "通用 ZIP 壓縮/解壓縮 (無檔案名稱限制)",
                "記憶體壓縮/解壓縮",
                "Base64 編碼支援",
                "事件鉤子系統"
            ],
            "personas_count": len(self.connector.personas),
            "active_connections": len(self.connector.connections)
        }
    
    def quick_compress(
        self,
        files: Union[str, List[str], Dict[str, str]],
        output_name: Optional[str] = None
    ) -> str:
        """
        快速壓縮檔案
        
        Args:
            files: 檔案或資料
            output_name: 輸出檔名
            
        Returns:
            壓縮檔案路徑
        """
        result = self.zip_handler.compress(files, output_name)
        return result["output_path"] if result["success"] else None
    
    def quick_decompress(self, zip_path: str, output_dir: Optional[str] = None) -> str:
        """
        快速解壓縮
        
        Args:
            zip_path: ZIP 檔案路徑
            output_dir: 輸出目錄
            
        Returns:
            解壓縮目錄路徑
        """
        result = self.zip_handler.decompress(zip_path, output_dir)
        return result["output_dir"] if result["success"] else None


def interactive_demo():
    """互動式示範"""
    print("=" * 60)
    print("  MRLiou AI 模組人格通用套件 - 互動示範")
    print("=" * 60)
    print()
    
    toolkit = AIPersonaToolkit()
    
    while True:
        print("\n【主選單】")
        print("1. 人格管理")
        print("2. ZIP 壓縮")
        print("3. ZIP 解壓縮")
        print("4. 列出 ZIP 內容")
        print("5. 套件資訊")
        print("q. 離開")
        
        choice = input("\n請選擇功能: ").strip()
        
        if choice == "1":
            _persona_menu(toolkit.connector)
        elif choice == "2":
            _compress_menu(toolkit.zip_handler)
        elif choice == "3":
            _decompress_menu(toolkit.zip_handler)
        elif choice == "4":
            _list_zip_menu(toolkit.zip_handler)
        elif choice == "5":
            info = toolkit.get_info()
            print("\n【套件資訊】")
            print(f"  名稱: {info['name']}")
            print(f"  中文名: {info['name_zh']}")
            print(f"  版本: {info['version']}")
            print(f"  功能:")
            for feature in info['features']:
                print(f"    - {feature}")
        elif choice.lower() == "q":
            print("\n感謝使用！")
            break
        else:
            print("\n❌ 無效的選項")


def _persona_menu(connector: PersonaConnector):
    """人格管理子選單"""
    while True:
        print("\n【人格管理】")
        print("1. 註冊新人格")
        print("2. 連接人格")
        print("3. 切換人格")
        print("4. 列出人格")
        print("5. 斷開連接")
        print("b. 返回")
        
        choice = input("\n請選擇: ").strip()
        
        if choice == "1":
            pid = input("人格 ID: ").strip()
            name = input("人格名稱: ").strip()
            role = input("角色（用逗號分隔）: ").strip()
            traits = input("特質（用逗號分隔）: ").strip()
            
            result = connector.register_persona(
                persona_id=pid,
                name=name,
                role=[r.strip() for r in role.split(",") if r.strip()],
                traits=[t.strip() for t in traits.split(",") if t.strip()]
            )
            print(f"\n✅ {result['message']}")
            
        elif choice == "2":
            pid = input("人格 ID: ").strip()
            result = connector.connect(pid)
            if result["success"]:
                print(f"\n✅ {result['message']}")
            else:
                print(f"\n❌ {result['error']}")
                
        elif choice == "3":
            pid = input("人格 ID: ").strip()
            result = connector.switch_persona(pid)
            if result["success"]:
                print(f"\n✅ {result['message']}")
            else:
                print(f"\n❌ {result['error']}")
                
        elif choice == "4":
            personas = connector.list_personas()
            if not personas:
                print("\n目前沒有已註冊的人格")
            else:
                print(f"\n找到 {len(personas)} 個人格:")
                for p in personas:
                    status = "🟢" if p["status"] == "active" else "⚪"
                    print(f"  {status} [{p['id']}] {p['name']} - {', '.join(p['role'])}")
                    
        elif choice == "5":
            pid = input("人格 ID: ").strip()
            result = connector.disconnect(pid)
            if result["success"]:
                print(f"\n✅ {result['message']}")
            else:
                print(f"\n❌ {result['error']}")
                
        elif choice.lower() == "b":
            break


def _compress_menu(handler: UniversalZipHandler):
    """壓縮子選單"""
    print("\n【ZIP 壓縮】")
    print("1. 壓縮檔案/目錄")
    print("2. 壓縮文字資料")
    
    choice = input("\n請選擇: ").strip()
    
    if choice == "1":
        paths = input("輸入檔案或目錄路徑（用逗號分隔）: ").strip()
        path_list = [p.strip() for p in paths.split(",") if p.strip()]
        output = input("輸出檔名（留空自動生成）: ").strip() or None
        
        result = handler.compress(path_list, output)
        if result["success"]:
            print(f"\n✅ 壓縮完成!")
            print(f"   輸出: {result['output_path']}")
            print(f"   檔案數: {result['files_count']}")
            print(f"   壓縮後大小: {result['compressed_size']} bytes")
        else:
            print(f"\n❌ 壓縮失敗: {result.get('error', '未知錯誤')}")
            
    elif choice == "2":
        print("輸入資料（格式: 檔名=內容，每行一個）:")
        data = {}
        while True:
            line = input("  > ").strip()
            if not line:
                break
            if "=" in line:
                fname, content = line.split("=", 1)
                data[fname.strip()] = content.strip()
        
        if data:
            output = input("輸出檔名（留空自動生成）: ").strip() or None
            result = handler.compress(data, output)
            if result["success"]:
                print(f"\n✅ 壓縮完成: {result['output_path']}")


def _decompress_menu(handler: UniversalZipHandler):
    """解壓縮子選單"""
    print("\n【ZIP 解壓縮】")
    zip_path = input("輸入 ZIP 檔案路徑: ").strip()
    output_dir = input("輸出目錄（留空自動生成）: ").strip() or None
    
    result = handler.decompress(zip_path, output_dir)
    if result["success"]:
        print(f"\n✅ 解壓縮完成!")
        print(f"   輸出目錄: {result['output_dir']}")
        print(f"   檔案數: {result['files_count']}")
        if result["skipped"]:
            print(f"   跳過: {len(result['skipped'])} 個檔案")
    else:
        print(f"\n❌ 解壓縮失敗: {result['error']}")


def _list_zip_menu(handler: UniversalZipHandler):
    """列出 ZIP 內容"""
    print("\n【列出 ZIP 內容】")
    zip_path = input("輸入 ZIP 檔案路徑: ").strip()
    
    result = handler.list_contents(zip_path)
    if result["success"]:
        print(f"\n📦 {zip_path} ({result['count']} 個項目):")
        for item in result["contents"]:
            type_icon = "📁" if item["is_dir"] else "📄"
            size_info = f"({item['size']} bytes)" if not item["is_dir"] else ""
            print(f"  {type_icon} {item['filename']} {size_info}")
    else:
        print(f"\n❌ {result['error']}")


def main():
    """主函數"""
    print("=" * 60)
    print("  MRLiou AI 模組人格通用套件 v1.0")
    print("=" * 60)
    print()
    
    # 建立套件實例
    toolkit = AIPersonaToolkit()
    
    # 示範：註冊人格
    print("【示範：人格連結器】")
    print()
    
    # 註冊示範人格
    result = toolkit.connector.register_persona(
        persona_id="demo_assistant",
        name="Demo Assistant",
        role=["助手", "教學"],
        traits=["友善", "專業", "耐心"],
        modules=["NLP", "Knowledge"]
    )
    print(f"1. 註冊人格: {result['message']}")
    
    # 連接人格
    result = toolkit.connector.connect("demo_assistant")
    print(f"2. 連接人格: {result['message']}")
    
    # 切換人格
    result = toolkit.connector.switch_persona("demo_assistant")
    print(f"3. 切換人格: {result['message']}")
    
    # 獲取活動人格
    active = toolkit.connector.get_active_persona()
    print(f"4. 活動人格: {active['name']} ({', '.join(active['role'])})")
    
    print()
    print("【示範：ZIP 壓縮/解壓縮】")
    print()
    
    # 壓縮資料到記憶體
    test_data = {
        "hello.txt": "Hello, World!",
        "data.json": '{"name": "MRLiou", "version": "1.0"}',
        "中文檔案.txt": "這是中文內容測試",
        "special!@#$.txt": "特殊檔名測試"
    }
    
    result = toolkit.zip_handler.compress(test_data, "demo_archive.zip")
    print(f"1. 壓縮資料:")
    print(f"   - 檔案數: {result['files_count']}")
    print(f"   - 輸出: {result['output_path']}")
    print(f"   - 壓縮後大小: {result['compressed_size']} bytes")
    
    # 列出內容
    result = toolkit.zip_handler.list_contents("demo_archive.zip")
    print(f"\n2. ZIP 內容 ({result['count']} 個檔案):")
    for item in result["contents"]:
        print(f"   - {item['filename']} ({item['size']} bytes)")
    
    # 解壓縮
    result = toolkit.zip_handler.decompress("demo_archive.zip", "demo_extracted")
    print(f"\n3. 解壓縮完成:")
    print(f"   - 輸出目錄: {result['output_dir']}")
    print(f"   - 解壓檔案數: {result['files_count']}")
    
    # Base64 壓縮/解壓
    print(f"\n4. Base64 壓縮:")
    b64_data = toolkit.zip_handler.compress_to_base64({"test.txt": "Base64 test"})
    print(f"   - Base64 長度: {len(b64_data)} 字元")
    print(f"   - 預覽: {b64_data[:50]}...")
    
    print()
    print("【套件資訊】")
    info = toolkit.get_info()
    print(f"  版本: {info['version']}")
    print(f"  功能: {', '.join(info['features'][:3])}...")
    
    print()
    print("=" * 60)
    print("  執行 'python ai_persona_toolkit.py interactive' 進入互動模式")
    print("=" * 60)
    
    # 清理示範檔案
    if os.path.exists("demo_archive.zip"):
        os.remove("demo_archive.zip")
    if os.path.exists("demo_extracted"):
        shutil.rmtree("demo_extracted")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        interactive_demo()
    else:
        main()
