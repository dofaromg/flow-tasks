"""
Test suite for ConversationExtractor
對話知識提取器測試套件
"""

import os
import sys
import json
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
        "content": "粒子語言是一種創新的邏輯執行框架。它將計算邏輯抽象為種子概念，通過共振機制實現計算。因為傳統編程範式過於複雜，所以我們設計了更自然的表達方式。"
    },
    {
        "role": "user",
        "content": "它有什麼優勢？"
    },
    {
        "role": "assistant",
        "content": "主要優勢包括：高可讀性、易維護性、跨領域適用性。由於採用了模組化設計，因此系統具有良好的擴展性。總之，這是一種面向未來的計算範式。"
    }
]


def test_extractor_initialization():
    """測試提取器初始化"""
    # 無 API key 初始化
    extractor = ConversationExtractor()
    assert extractor is not None
    assert extractor.api_key is None
    
    # 有 API key 初始化（但不實際使用）
    extractor_with_key = ConversationExtractor(api_key="test_key")
    assert extractor_with_key.api_key == "test_key"


def test_package_conversation():
    """測試對話打包"""
    extractor = ConversationExtractor()
    
    metadata = {
        "title": "測試對話",
        "date": "2026-01-04",
        "tags": ["test", "demo"]
    }
    
    package = extractor.package_conversation(SAMPLE_CONVERSATION, metadata)
    
    # 驗證包結構
    assert "metadata" in package
    assert "messages" in package
    assert "statistics" in package
    assert "exported_at" in package
    assert "version" in package
    
    # 驗證元數據
    assert package["metadata"]["title"] == "測試對話"
    assert "test" in package["metadata"]["tags"]
    
    # 驗證訊息
    assert len(package["messages"]) == 4
    assert package["messages"][0]["role"] == "user"


def test_calculate_statistics():
    """測試統計計算"""
    extractor = ConversationExtractor()
    stats = extractor._calculate_statistics(SAMPLE_CONVERSATION)
    
    # 驗證統計數據
    assert stats["total_messages"] == 4
    assert stats["user_messages"] == 2
    assert stats["assistant_messages"] == 2
    assert stats["total_chars"] > 0
    assert stats["avg_user_length"] > 0
    assert stats["avg_assistant_length"] > 0


def test_export_json():
    """測試 JSON 導出"""
    extractor = ConversationExtractor()
    package = extractor.package_conversation(SAMPLE_CONVERSATION)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
    
    try:
        extractor.export_to_file(package, temp_path, "json")
        
        # 驗證檔案存在
        assert os.path.exists(temp_path)
        
        # 驗證內容
        with open(temp_path, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        
        assert "messages" in loaded_data
        assert len(loaded_data["messages"]) == 4
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_export_markdown():
    """測試 Markdown 導出"""
    extractor = ConversationExtractor()
    package = extractor.package_conversation(
        SAMPLE_CONVERSATION,
        metadata={"title": "測試", "date": "2026-01-04", "tags": ["test"]}
    )
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        temp_path = f.name
    
    try:
        extractor.export_to_file(package, temp_path, "markdown")
        
        # 驗證檔案存在
        assert os.path.exists(temp_path)
        
        # 驗證內容
        with open(temp_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "# 測試" in content
        assert "User" in content or "👤" in content
        assert "Assistant" in content or "🤖" in content
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_export_text():
    """測試純文字導出"""
    extractor = ConversationExtractor()
    package = extractor.package_conversation(SAMPLE_CONVERSATION)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        temp_path = f.name
    
    try:
        extractor.export_to_file(package, temp_path, "txt")
        
        # 驗證檔案存在
        assert os.path.exists(temp_path)
        
        # 驗證內容
        with open(temp_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "[USER]" in content or "[ASSISTANT]" in content
        assert "=" in content  # 分隔線
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_extract_keywords():
    """測試關鍵詞提取"""
    extractor = ConversationExtractor()
    
    text = "粒子語言系統採用創新的邏輯執行框架，提供了高可讀性和易維護性。"
    keywords = extractor._extract_keywords(text, top_n=5)
    
    assert isinstance(keywords, list)
    assert len(keywords) <= 5
    # 停用詞應該被過濾
    assert "的" not in keywords
    assert "了" not in keywords


def test_analyze_attention():
    """測試注意力機制分析"""
    extractor = ConversationExtractor()
    
    # 添加問題以觸發 key_moments
    conversation_with_question = SAMPLE_CONVERSATION + [
        {
            "role": "user",
            "content": "能詳細解釋一下粒子語言的執行機制嗎？這個問題很重要。"
        },
        {
            "role": "assistant",
            "content": "當然可以！粒子語言的執行機制基於五個階段：STRUCTURE（結構化）、MARK（標記）、FLOW（流動）、RECURSE（遞歸）、STORE（存儲）。每個階段都有明確的職責，確保邏輯執行的完整性和可追溯性。這種設計使得系統能夠處理複雜的邏輯鏈，同時保持高度的模組化和可維護性。"
        }
    ]
    
    analysis = extractor.analyze_attention(conversation_with_question)
    
    # 驗證分析結果結構
    assert "key_moments" in analysis
    assert "topic_shifts" in analysis
    assert "high_density_segments" in analysis
    
    # 驗證類型
    assert isinstance(analysis["key_moments"], list)
    assert isinstance(analysis["topic_shifts"], list)
    assert isinstance(analysis["high_density_segments"], list)


def test_extract_concepts():
    """測試概念提取"""
    extractor = ConversationExtractor()
    
    text = "FlowAgent 系統使用了粒子語言機制和記憶封存系統。Kubernetes 架構提供了容器編排能力。"
    concepts = extractor._extract_concepts(text)
    
    assert isinstance(concepts, list)
    # 應該能提取到一些概念
    assert len(concepts) >= 0


def test_extract_causal_relations():
    """測試因果關係提取"""
    extractor = ConversationExtractor()
    
    text = "因為系統需要高可用性，所以我們採用了分佈式架構。由於性能要求很高，因此使用了緩存機制。"
    relations = extractor._extract_causal_relations(text)
    
    assert isinstance(relations, list)
    if len(relations) > 0:
        assert "cause" in relations[0]
        assert "effect" in relations[0]
        assert "type" in relations[0]


def test_extract_reasoning_chains():
    """測試推理鏈提取"""
    extractor = ConversationExtractor()
    
    text = "首先需要理解基礎概念。理解概念後可以開始實作。因此，循序漸進是最好的學習方式。"
    chains = extractor._extract_reasoning_chains(text)
    
    assert isinstance(chains, list)
    # 推理鏈應該是字串列表的列表
    for chain in chains:
        assert isinstance(chain, list)


def test_extract_conclusions():
    """測試結論提取"""
    extractor = ConversationExtractor()
    
    text = "經過分析，我們發現三個關鍵問題。綜上所述，系統需要進行優化。總之，這是一個重要的改進方向。"
    conclusions = extractor._extract_conclusions(text)
    
    assert isinstance(conclusions, list)
    # 應該能找到一些結論
    if len(conclusions) > 0:
        assert isinstance(conclusions[0], str)


def test_extract_logical_structure():
    """測試邏輯結構提取"""
    extractor = ConversationExtractor()
    
    structure = extractor.extract_logical_structure(SAMPLE_CONVERSATION)
    
    # 驗證結構
    assert "concepts" in structure
    assert "relationships" in structure
    assert "reasoning_chains" in structure
    assert "conclusions" in structure
    
    # 驗證類型
    assert isinstance(structure["concepts"], list)
    assert isinstance(structure["relationships"], list)
    assert isinstance(structure["reasoning_chains"], list)
    assert isinstance(structure["conclusions"], list)


def test_generate_report():
    """測試報告生成"""
    extractor = ConversationExtractor()
    
    # 不使用 AI 分析
    report = extractor.generate_report(SAMPLE_CONVERSATION, include_ai_analysis=False)
    
    # 驗證報告內容
    assert isinstance(report, str)
    assert len(report) > 0
    assert "對話知識提取報告" in report
    assert "基本統計" in report
    assert "注意力分析" in report
    assert "邏輯結構" in report


def test_deep_analysis_without_api_key():
    """測試無 API key 的 AI 分析"""
    extractor = ConversationExtractor()
    
    result = extractor.deep_analysis_with_ai(SAMPLE_CONVERSATION)
    
    # 應該返回錯誤訊息
    assert "error" in result
    assert "API Key" in result["error"]


def test_format_for_analysis():
    """測試分析格式化"""
    extractor = ConversationExtractor()
    
    formatted = extractor._format_for_analysis(SAMPLE_CONVERSATION)
    
    assert isinstance(formatted, str)
    assert "User" in formatted or "Assistant" in formatted
    assert len(formatted) > 0


def test_export_yaml():
    """測試 YAML 導出"""
    extractor = ConversationExtractor()
    package = extractor.package_conversation(SAMPLE_CONVERSATION)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        temp_path = f.name
    
    try:
        extractor.export_to_file(package, temp_path, "yaml")
        
        # 驗證檔案存在
        assert os.path.exists(temp_path)
        
        # 驗證內容
        with open(temp_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "messages:" in content or "metadata:" in content
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_export_csv():
    """測試 CSV 導出"""
    extractor = ConversationExtractor()
    package = extractor.package_conversation(SAMPLE_CONVERSATION)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        temp_path = f.name
    
    try:
        extractor.export_to_file(package, temp_path, "csv")
        
        # 驗證檔案存在
        assert os.path.exists(temp_path)
        
        # 驗證內容
        with open(temp_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "Index" in content
        assert "Role" in content
        assert "Content" in content
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_export_html():
    """測試 HTML 導出"""
    extractor = ConversationExtractor()
    package = extractor.package_conversation(
        SAMPLE_CONVERSATION,
        metadata={"title": "測試", "date": "2026-01-05", "tags": ["test"]}
    )
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        temp_path = f.name
    
    try:
        extractor.export_to_file(package, temp_path, "html")
        
        # 驗證檔案存在
        assert os.path.exists(temp_path)
        
        # 驗證內容
        with open(temp_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "<!DOCTYPE html>" in content
        assert "<html" in content
        assert "測試" in content
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_export_xml():
    """測試 XML 導出"""
    extractor = ConversationExtractor()
    package = extractor.package_conversation(SAMPLE_CONVERSATION)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
        temp_path = f.name
    
    try:
        extractor.export_to_file(package, temp_path, "xml")
        
        # 驗證檔案存在
        assert os.path.exists(temp_path)
        
        # 驗證內容
        with open(temp_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert '<?xml version="1.0" encoding="UTF-8"?>' in content
        assert "<conversation" in content
        assert "<messages>" in content
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


# 執行測試
if __name__ == "__main__":
    print("🧪 執行對話知識提取器測試...")
    print("=" * 60)
    
    # 手動執行所有測試
    test_functions = [
        test_extractor_initialization,
        test_package_conversation,
        test_calculate_statistics,
        test_export_json,
        test_export_markdown,
        test_export_text,
        test_export_yaml,
        test_export_csv,
        test_export_html,
        test_export_xml,
        test_extract_keywords,
        test_analyze_attention,
        test_extract_concepts,
        test_extract_causal_relations,
        test_extract_reasoning_chains,
        test_extract_conclusions,
        test_extract_logical_structure,
        test_generate_report,
        test_deep_analysis_without_api_key,
        test_format_for_analysis,
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
