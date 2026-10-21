"""
Test suite for ConversationExtractor Import/Export functionality
對話知識提取器導入/導出功能測試套件
"""

import os
import sys
import tempfile

# Add particle_core/src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from conversation_extractor import ConversationExtractor


# Sample conversation data for testing
SAMPLE_CONVERSATION = [
    {
        "role": "user",
        "content": "什麼是粒子語言？"
    },
    {
        "role": "assistant",
        "content": "粒子語言是一種創新的邏輯執行框架。"
    },
    {
        "role": "user",
        "content": "它有什麼優勢？"
    },
    {
        "role": "assistant",
        "content": "主要優勢包括：高可讀性、易維護性、跨領域適用性。"
    }
]


def test_export_csv():
    """測試 CSV 導出"""
    extractor = ConversationExtractor()
    package = extractor.package_conversation(SAMPLE_CONVERSATION)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        temp_path = f.name
    
    try:
        extractor.export_to_file(package, temp_path, "csv")
        assert os.path.exists(temp_path)
        
        # 驗證內容
        with open(temp_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert 'role' in content
        assert 'content' in content
        assert 'user' in content
        assert 'assistant' in content
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_export_xml():
    """測試 XML 導出"""
    extractor = ConversationExtractor()
    package = extractor.package_conversation(
        SAMPLE_CONVERSATION,
        metadata={"title": "測試", "date": "2026-01-05", "tags": ["test"]}
    )
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
        temp_path = f.name
    
    try:
        extractor.export_to_file(package, temp_path, "xml")
        assert os.path.exists(temp_path)
        
        # 驗證內容
        with open(temp_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert '<?xml' in content
        assert '<conversation>' in content
        assert '<message' in content
        assert '<metadata>' in content
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_export_yaml():
    """測試 YAML 導出"""
    extractor = ConversationExtractor()
    package = extractor.package_conversation(SAMPLE_CONVERSATION)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        temp_path = f.name
    
    try:
        extractor.export_to_file(package, temp_path, "yaml")
        assert os.path.exists(temp_path)
        
        # 驗證內容
        with open(temp_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert 'messages' in content
        assert 'role:' in content
        assert 'content:' in content
    except ImportError:
        print("  ⊘ YAML 測試跳過（PyYAML 未安裝）")


def test_import_json():
    """測試 JSON 導入"""
    extractor = ConversationExtractor()
    package = extractor.package_conversation(SAMPLE_CONVERSATION)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
    
    try:
        # 導出
        extractor.export_to_file(package, temp_path, "json")
        
        # 導入
        imported = extractor.import_from_file(temp_path, "json")
        
        # 驗證
        assert "messages" in imported
        assert len(imported["messages"]) == 4
        assert imported["messages"][0]["role"] == "user"
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_import_markdown():
    """測試 Markdown 導入"""
    extractor = ConversationExtractor()
    package = extractor.package_conversation(
        SAMPLE_CONVERSATION,
        metadata={"title": "測試對話", "date": "2026-01-05", "tags": ["test"]}
    )
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        temp_path = f.name
    
    try:
        # 導出
        extractor.export_to_file(package, temp_path, "markdown")
        
        # 導入
        imported = extractor.import_from_file(temp_path, "markdown")
        
        # 驗證
        assert "messages" in imported
        assert len(imported["messages"]) >= 2  # 至少有部分訊息
        assert "metadata" in imported
        assert imported["metadata"].get("title") == "測試對話"
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_import_text():
    """測試純文字導入"""
    extractor = ConversationExtractor()
    
    # 測試 [USER]/[ASSISTANT] 格式
    text_content = """[USER]
這是用戶問題

==================================================

[ASSISTANT]
這是助手回答

==================================================
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(text_content)
        temp_path = f.name
    
    try:
        imported = extractor.import_from_file(temp_path, "txt")
        
        assert "messages" in imported
        assert len(imported["messages"]) >= 2
        assert imported["messages"][0]["role"] == "user"
        assert imported["messages"][1]["role"] == "assistant"
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_import_csv():
    """測試 CSV 導入"""
    extractor = ConversationExtractor()
    package = extractor.package_conversation(SAMPLE_CONVERSATION)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        temp_path = f.name
    
    try:
        # 導出
        extractor.export_to_file(package, temp_path, "csv")
        
        # 導入
        imported = extractor.import_from_file(temp_path, "csv")
        
        # 驗證
        assert "messages" in imported
        assert len(imported["messages"]) == 4
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_import_xml():
    """測試 XML 導入"""
    extractor = ConversationExtractor()
    package = extractor.package_conversation(
        SAMPLE_CONVERSATION,
        metadata={"title": "XML測試", "date": "2026-01-05", "tags": ["xml", "test"]}
    )
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
        temp_path = f.name
    
    try:
        # 導出
        extractor.export_to_file(package, temp_path, "xml")
        
        # 導入
        imported = extractor.import_from_file(temp_path, "xml")
        
        # 驗證
        assert "messages" in imported
        assert len(imported["messages"]) == 4
        assert "metadata" in imported
        assert imported["metadata"].get("title") == "XML測試"
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_import_yaml():
    """測試 YAML 導入"""
    extractor = ConversationExtractor()
    package = extractor.package_conversation(SAMPLE_CONVERSATION)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        temp_path = f.name
    
    try:
        # 導出
        extractor.export_to_file(package, temp_path, "yaml")
        
        # 導入
        imported = extractor.import_from_file(temp_path, "yaml")
        
        # 驗證
        assert "messages" in imported
        assert len(imported["messages"]) == 4
    except ImportError:
        print("  ⊘ YAML 測試跳過（PyYAML 未安裝）")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_auto_detect_format():
    """測試自動格式檢測"""
    extractor = ConversationExtractor()
    
    # 測試不同副檔名
    test_cases = [
        ('test.json', 'json'),
        ('test.md', 'markdown'),
        ('test.markdown', 'markdown'),
        ('test.txt', 'txt'),
        ('test.csv', 'csv'),
        ('test.xml', 'xml'),
        ('test.yaml', 'yaml'),
        ('test.yml', 'yaml'),
    ]
    
    for filename, expected_format in test_cases:
        detected = extractor._detect_format(filename)
        assert detected == expected_format, f"{filename} 應該被檢測為 {expected_format}，但得到 {detected}"


def test_roundtrip_json():
    """測試 JSON 往返"""
    extractor = ConversationExtractor()
    original = extractor.package_conversation(SAMPLE_CONVERSATION)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
    
    try:
        # 導出
        extractor.export_to_file(original, temp_path, "json")
        
        # 導入
        imported = extractor.import_from_file(temp_path, "json")
        
        # 驗證往返
        assert len(original["messages"]) == len(imported["messages"])
        for i in range(len(original["messages"])):
            assert original["messages"][i]["role"] == imported["messages"][i]["role"]
            assert original["messages"][i]["content"] == imported["messages"][i]["content"]
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_roundtrip_csv():
    """測試 CSV 往返"""
    extractor = ConversationExtractor()
    original = SAMPLE_CONVERSATION
    package = extractor.package_conversation(original)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        temp_path = f.name
    
    try:
        # 導出
        extractor.export_to_file(package, temp_path, "csv")
        
        # 導入
        imported = extractor.import_from_file(temp_path, "csv")
        
        # 驗證往返
        assert len(original) == len(imported["messages"])
        for i in range(len(original)):
            assert original[i]["role"] == imported["messages"][i]["role"]
            assert original[i]["content"] == imported["messages"][i]["content"]
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_text_format_user_assistant():
    """測試 User:/Assistant: 文字格式"""
    extractor = ConversationExtractor()
    
    text_content = """User: 這是第一個問題
Assistant: 這是第一個回答

User: 這是第二個問題
Assistant: 這是第二個回答
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(text_content)
        temp_path = f.name
    
    try:
        imported = extractor.import_from_file(temp_path, "txt")
        
        assert len(imported["messages"]) == 4
        assert imported["messages"][0]["role"] == "user"
        assert imported["messages"][1]["role"] == "assistant"
        assert "第一個問題" in imported["messages"][0]["content"]
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


# 執行測試
if __name__ == "__main__":
    print("🧪 執行對話知識提取器導入/導出測試...")
    print("=" * 60)
    
    # 手動執行所有測試
    test_functions = [
        test_export_csv,
        test_export_xml,
        test_export_yaml,
        test_import_json,
        test_import_markdown,
        test_import_text,
        test_import_csv,
        test_import_xml,
        test_import_yaml,
        test_auto_detect_format,
        test_roundtrip_json,
        test_roundtrip_csv,
        test_text_format_user_assistant,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in test_functions:
        try:
            test_func()
            print(f"✓ {test_func.__name__}")
            passed += 1
        except Exception as e:
            print(f"✗ {test_func.__name__}: {e}")
            failed += 1
    
    print("=" * 60)
    print(f"測試結果: {passed} 通過, {failed} 失敗")
    
    if failed == 0:
        print("✅ 所有測試通過！")
    else:
        print(f"⚠️  有 {failed} 個測試失敗")
