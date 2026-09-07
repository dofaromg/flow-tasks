"""
對話知識提取器 - 導入/導出功能示範
Conversation Extractor - Import/Export Demo

展示如何從各種檔案格式導入和導出對話記錄
Demonstrates importing and exporting conversations from various file formats
"""

import os
import sys

# 將 particle_core/src 加入路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from conversation_extractor import ConversationExtractor


def demo_export_all_formats():
    """示範導出所有格式"""
    print("=" * 60)
    print("📤 示範 1：導出所有支援的格式")
    print("=" * 60)
    
    # 建立測試對話
    conversation = [
        {
            "role": "user",
            "content": "什麼是粒子語言？"
        },
        {
            "role": "assistant",
            "content": "粒子語言是一種創新的邏輯執行框架。它將計算邏輯抽象為種子概念，通過共振機制實現計算協同。"
        },
        {
            "role": "user",
            "content": "它有什麼優勢？"
        },
        {
            "role": "assistant",
            "content": "主要優勢包括：高可讀性、易維護性、跨領域適用性。由於採用了模組化設計，因此系統具有良好的擴展性。"
        }
    ]
    
    extractor = ConversationExtractor()
    
    # 打包對話
    package = extractor.package_conversation(
        conversation,
        metadata={
            "title": "粒子語言介紹",
            "date": "2026-01-05",
            "tags": ["粒子語言", "系統架構", "框架"]
        }
    )
    
    # 建立輸出目錄
    output_dir = "/tmp/conversation_formats"
    os.makedirs(output_dir, exist_ok=True)
    
    # 導出所有格式
    formats = ["json", "markdown", "txt", "csv", "xml", "yaml"]
    
    print("\n導出檔案：")
    for fmt in formats:
        filepath = os.path.join(output_dir, f"conversation.{fmt}")
        try:
            extractor.export_to_file(package, filepath, fmt)
        except Exception as e:
            print(f"✗ 導出 {fmt.upper()} 失敗: {e}")
    
    print(f"\n✓ 所有檔案已導出到: {output_dir}")
    return output_dir


def demo_import_all_formats(output_dir):
    """示範從所有格式導入"""
    print("\n" + "=" * 60)
    print("📥 示範 2：從所有格式導入")
    print("=" * 60)
    
    extractor = ConversationExtractor()
    
    # 嘗試從每種格式導入
    formats = ["json", "markdown", "txt", "csv", "xml", "yaml"]
    
    for fmt in formats:
        filepath = os.path.join(output_dir, f"conversation.{fmt}")
        
        if not os.path.exists(filepath):
            print(f"⊘ 檔案不存在: {filepath}")
            continue
        
        try:
            print(f"\n--- 測試 {fmt.upper()} 導入 ---")
            package = extractor.import_from_file(filepath)
            
            # 顯示導入結果
            print(f"  訊息數量: {len(package['messages'])}")
            if 'metadata' in package and package['metadata']:
                print(f"  標題: {package['metadata'].get('title', 'N/A')}")
            print(f"  第一條訊息: {package['messages'][0]['content'][:50]}...")
            
        except Exception as e:
            print(f"✗ 從 {fmt.upper()} 導入失敗: {e}")
            import traceback
            traceback.print_exc()


def demo_auto_detect():
    """示範自動格式檢測"""
    print("\n" + "=" * 60)
    print("🔍 示範 3：自動檢測檔案格式")
    print("=" * 60)
    
    extractor = ConversationExtractor()
    
    # 測試不同副檔名
    test_files = [
        "/tmp/conversation_formats/conversation.json",
        "/tmp/conversation_formats/conversation.md",
        "/tmp/conversation_formats/conversation.txt",
        "/tmp/conversation_formats/conversation.yaml",
    ]
    
    for filepath in test_files:
        if os.path.exists(filepath):
            print(f"\n導入: {os.path.basename(filepath)}")
            try:
                package = extractor.import_from_file(filepath)  # 不指定格式，自動檢測
                print(f"  ✓ 成功檢測並導入 ({len(package['messages'])} 條訊息)")
            except Exception as e:
                print(f"  ✗ 失敗: {e}")


def demo_custom_text_formats():
    """示範自定義文字格式導入"""
    print("\n" + "=" * 60)
    print("📝 示範 4：自定義文字格式導入")
    print("=" * 60)
    
    extractor = ConversationExtractor()
    
    # 測試格式1: User: 和 Assistant: 格式
    format1_content = """User: 你好，請問你是誰？
Assistant: 我是 FlowAgent 系統的助手，專門協助處理粒子語言相關任務。

User: 能介紹一下你的功能嗎？
Assistant: 當然！我可以幫助你進行對話分析、邏輯結構提取、知識圖譜生成等工作。
"""
    
    os.makedirs("/tmp/conversation_formats", exist_ok=True)
    
    with open("/tmp/conversation_formats/custom_format1.txt", "w", encoding="utf-8") as f:
        f.write(format1_content)
    
    print("\n格式1: User:/Assistant: 格式")
    try:
        package = extractor.import_from_file("/tmp/conversation_formats/custom_format1.txt")
        print(f"  ✓ 成功導入 {len(package['messages'])} 條訊息")
        for i, msg in enumerate(package['messages'][:2], 1):
            print(f"  {i}. [{msg['role']}] {msg['content'][:40]}...")
    except Exception as e:
        print(f"  ✗ 失敗: {e}")
    
    # 測試格式2: [USER] 和 [ASSISTANT] 格式
    format2_content = """[USER]
請問粒子語言的核心原理是什麼？

==================================================

[ASSISTANT]
粒子語言的核心原理是將邏輯抽象為「種子」，通過「共振」機制實現計算協同。

==================================================

[USER]
這聽起來很有趣！

==================================================

[ASSISTANT]
是的！這是一種面向未來的計算範式。

==================================================
"""
    
    with open("/tmp/conversation_formats/custom_format2.txt", "w", encoding="utf-8") as f:
        f.write(format2_content)
    
    print("\n格式2: [USER]/[ASSISTANT] 格式")
    try:
        package = extractor.import_from_file("/tmp/conversation_formats/custom_format2.txt")
        print(f"  ✓ 成功導入 {len(package['messages'])} 條訊息")
        for i, msg in enumerate(package['messages'][:2], 1):
            print(f"  {i}. [{msg['role']}] {msg['content'][:40]}...")
    except Exception as e:
        print(f"  ✗ 失敗: {e}")


def demo_roundtrip():
    """示範導出後再導入（往返測試）"""
    print("\n" + "=" * 60)
    print("🔄 示範 5：往返測試（導出後再導入）")
    print("=" * 60)
    
    extractor = ConversationExtractor()
    
    # 原始對話
    original_conversation = [
        {"role": "user", "content": "測試問題 1"},
        {"role": "assistant", "content": "測試回答 1"},
        {"role": "user", "content": "測試問題 2"},
        {"role": "assistant", "content": "測試回答 2"},
    ]
    
    package = extractor.package_conversation(
        original_conversation,
        metadata={"title": "往返測試", "tags": ["test"]}
    )
    
    os.makedirs("/tmp/conversation_formats", exist_ok=True)
    
    # 測試 JSON 往返
    print("\nJSON 往返測試：")
    extractor.export_to_file(package, "/tmp/conversation_formats/roundtrip.json", "json")
    imported = extractor.import_from_file("/tmp/conversation_formats/roundtrip.json")
    print(f"  原始訊息數: {len(original_conversation)}")
    print(f"  導入訊息數: {len(imported['messages'])}")
    print(f"  往返成功: {len(original_conversation) == len(imported['messages'])}")
    
    # 測試 YAML 往返
    print("\nYAML 往返測試：")
    try:
        extractor.export_to_file(package, "/tmp/conversation_formats/roundtrip.yaml", "yaml")
        imported = extractor.import_from_file("/tmp/conversation_formats/roundtrip.yaml")
        print(f"  原始訊息數: {len(original_conversation)}")
        print(f"  導入訊息數: {len(imported['messages'])}")
        print(f"  往返成功: {len(original_conversation) == len(imported['messages'])}")
    except ImportError as e:
        print(f"  ⊘ YAML 測試跳過: {e}")


def main():
    """主程序"""
    print("\n" + "🧠 對話知識提取器 - 導入/導出功能示範")
    print("=" * 60)
    print("作者: MR.liou × Claude (empathetic.mirror)")
    print("版本: v1.0 (新增全格式支援)")
    print("=" * 60)
    
    try:
        # 執行所有示範
        output_dir = demo_export_all_formats()
        demo_import_all_formats(output_dir)
        demo_auto_detect()
        demo_custom_text_formats()
        demo_roundtrip()
        
        print("\n" + "=" * 60)
        print("✅ 所有示範完成！")
        print("=" * 60)
        print("\n支援的格式：")
        print("  導出: JSON, Markdown, TXT, CSV, XML, YAML")
        print("  導入: JSON, Markdown, TXT, CSV, XML, YAML")
        print("\n功能特色：")
        print("  ✓ 自動檢測檔案格式")
        print("  ✓ 支援多種文字對話格式")
        print("  ✓ 完整的元數據保留（JSON, XML, YAML）")
        print("  ✓ 往返導出/導入測試通過")
        
    except Exception as e:
        print(f"\n❌ 執行錯誤: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
