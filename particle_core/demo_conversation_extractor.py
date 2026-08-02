"""
對話知識提取器示範腳本
Conversation Extractor Demo Script

示範如何使用 ConversationExtractor 來分析和處理對話記錄
"""

import os
import sys

# 將 particle_core/src 加入路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from conversation_extractor import ConversationExtractor


def demo_basic_usage():
    """基本使用示範"""
    print("=" * 60)
    print("📚 示範 1：基本對話打包與導出")
    print("=" * 60)
    
    # 建立測試對話
    conversation = [
        {
            "role": "user",
            "content": "請問什麼是粒子語言核心系統？"
        },
        {
            "role": "assistant",
            "content": "粒子語言核心系統（Particle Language Core）是一個創新的邏輯執行框架。它將計算邏輯抽象為「種子」概念，通過「共振」機制實現跨領域的計算協同。系統採用五階段執行模式：STRUCTURE → MARK → FLOW → RECURSE → STORE，確保邏輯的完整性和可追溯性。"
        },
        {
            "role": "user",
            "content": "它和傳統的編程範式有什麼不同？"
        },
        {
            "role": "assistant",
            "content": "傳統編程範式專注於指令序列和數據結構，而粒子語言核心系統關注「邏輯種子」的組合與共振。因此，它更接近自然語言的表達方式，具有更好的可讀性和可維護性。此外，系統支持記憶封存和狀態恢復，可以在不同執行環境間無縫遷移。"
        }
    ]
    
    # 初始化提取器
    extractor = ConversationExtractor()
    
    # 打包對話
    package = extractor.package_conversation(
        conversation,
        metadata={
            "title": "粒子語言核心系統介紹",
            "date": "2026-01-04",
            "tags": ["粒子語言", "邏輯執行", "系統架構"]
        }
    )
    
    print(f"\n✓ 對話已打包")
    print(f"  - 總訊息數: {package['statistics']['total_messages']}")
    print(f"  - 總字符數: {package['statistics']['total_chars']}")
    print(f"  - 平均回覆長度: {package['statistics']['avg_assistant_length']:.0f} 字符")
    
    # 導出為不同格式
    os.makedirs("/tmp/conversation_demo", exist_ok=True)
    
    extractor.export_to_file(package, "/tmp/conversation_demo/demo.json", "json")
    extractor.export_to_file(package, "/tmp/conversation_demo/demo.md", "markdown")
    extractor.export_to_file(package, "/tmp/conversation_demo/demo.txt", "txt")
    extractor.export_to_file(package, "/tmp/conversation_demo/demo.yaml", "yaml")
    extractor.export_to_file(package, "/tmp/conversation_demo/demo.csv", "csv")
    extractor.export_to_file(package, "/tmp/conversation_demo/demo.html", "html")
    extractor.export_to_file(package, "/tmp/conversation_demo/demo.xml", "xml")
    
    print("\n✓ 已導出所有格式到 /tmp/conversation_demo/")


def demo_attention_analysis():
    """注意力機制分析示範"""
    print("\n" + "=" * 60)
    print("🎯 示範 2：注意力機制分析")
    print("=" * 60)
    
    conversation = [
        {
            "role": "user",
            "content": "我想學習如何部署 Kubernetes 應用？"
        },
        {
            "role": "assistant",
            "content": "部署 Kubernetes 應用需要理解幾個核心概念：Pod、Deployment、Service、ConfigMap 和 Secret。首先，Pod 是最小的部署單元，包含一個或多個容器。Deployment 管理 Pod 的副本和更新策略。Service 提供穩定的網路端點。ConfigMap 存儲配置數據，Secret 存儲敏感資訊。掌握這些基礎概念後，你就可以開始實際部署了。"
        },
        {
            "role": "user",
            "content": "那麼 GitOps 在這裡扮演什麼角色？"
        },
        {
            "role": "assistant",
            "content": "GitOps 是一種使用 Git 作為單一真實來源的運維實踐。因為所有的配置都存儲在 Git 倉庫中，所以可以追蹤每次變更的歷史。當配置被推送到 Git 後，自動化工具（如 Argo CD）會檢測變更並同步到集群。因此，這種方式提供了更好的可審計性和回滾能力。"
        },
        {
            "role": "user",
            "content": "聽起來很複雜，有什麼最佳實踐嗎？"
        },
        {
            "role": "assistant",
            "content": "最佳實踐包括：1) 使用命名空間隔離不同環境；2) 設置資源限制和請求；3) 使用 Health Check 確保服務可用性；4) 實施滾動更新策略；5) 建立完善的監控和日誌系統。總之，從小規模開始，逐步擴展是最穩妥的方法。"
        }
    ]
    
    extractor = ConversationExtractor()
    
    # 執行注意力分析
    attention = extractor.analyze_attention(conversation)
    
    print(f"\n📊 分析結果:")
    print(f"  - 關鍵時刻: {len(attention['key_moments'])} 個")
    print(f"  - 話題轉換: {len(attention['topic_shifts'])} 個")
    print(f"  - 資訊密集段落: {len(attention['high_density_segments'])} 個")
    
    if attention['key_moments']:
        print(f"\n💡 關鍵時刻範例:")
        for i, moment in enumerate(attention['key_moments'][:2], 1):
            print(f"  {i}. 問題: {moment['question'][:60]}...")
    
    if attention['topic_shifts']:
        print(f"\n🔄 話題轉換範例:")
        for i, shift in enumerate(attention['topic_shifts'][:2], 1):
            print(f"  {i}. 從 {shift['from_topics'][:2]} → {shift['to_topics'][:2]}")


def demo_logical_structure():
    """邏輯結構提取示範"""
    print("\n" + "=" * 60)
    print("🧬 示範 3：邏輯結構提取")
    print("=" * 60)
    
    conversation = [
        {
            "role": "user",
            "content": "為什麼系統需要記憶封存機制？"
        },
        {
            "role": "assistant",
            "content": "記憶封存機制的核心價值在於狀態保存和恢復。因為 AI 系統的運行狀態包含大量上下文資訊，所以需要一個有效的方式來持久化這些資訊。從技術角度看，記憶封存實現了狀態的快照、壓縮和傳輸。因此，系統可以在不同環境間遷移，或在失敗後快速恢復。"
        },
        {
            "role": "user",
            "content": "這和傳統的資料庫備份有什麼區別？"
        },
        {
            "role": "assistant",
            "content": "傳統備份關注數據完整性，而記憶封存關注邏輯連續性。由於 AI 系統的狀態不僅包括數據，還包括推理過程和上下文關係，因此需要更豐富的元數據來描述這些狀態。總之，記憶封存是一種更高層次的抽象，適合 AI 系統的特性。"
        }
    ]
    
    extractor = ConversationExtractor()
    
    # 提取邏輯結構
    structure = extractor.extract_logical_structure(conversation)
    
    print(f"\n📋 結構分析結果:")
    print(f"  - 核心概念: {len(structure['concepts'])} 個")
    print(f"  - 因果關係: {len(structure['relationships'])} 個")
    print(f"  - 推理鏈: {len(structure['reasoning_chains'])} 條")
    print(f"  - 結論: {len(structure['conclusions'])} 個")
    
    if structure['concepts']:
        print(f"\n🔑 核心概念範例:")
        for concept in structure['concepts'][:5]:
            print(f"  • {concept}")
    
    if structure['relationships']:
        print(f"\n⚡ 因果關係範例:")
        for i, rel in enumerate(structure['relationships'][:2], 1):
            print(f"  {i}. 原因: {rel['cause'][:40]}...")
            print(f"     結果: {rel['effect'][:40]}...")


def demo_report_generation():
    """報告生成示範"""
    print("\n" + "=" * 60)
    print("📊 示範 4：完整報告生成")
    print("=" * 60)
    
    conversation = [
        {
            "role": "user",
            "content": "MrLiouAI 系統的核心理念是什麼？"
        },
        {
            "role": "assistant",
            "content": "MrLiouAI 的核心理念是「共振式協同」。系統通過人格化的 AI 代理實現任務分解和執行。每個代理都有獨特的共振鍵，用於識別和連接。因此，多個代理可以協同工作，形成一個有機的計算生態系統。"
        },
        {
            "role": "user",
            "content": "這種設計有什麼優勢？"
        },
        {
            "role": "assistant",
            "content": "主要優勢包括：高度模組化、易於擴展、自然語言交互和跨領域適應。由於每個代理都是獨立的，所以系統具有很好的容錯性。總之，這種設計使得 AI 系統更加靈活和智慧。"
        }
    ]
    
    extractor = ConversationExtractor()
    
    # 生成報告（不包含 AI 分析，因為沒有 API key）
    report = extractor.generate_report(conversation, include_ai_analysis=False)
    
    print("\n✓ 報告已生成")
    print("\n--- 報告預覽 (前 500 字符) ---")
    print(report[:500])
    print("...\n")
    
    # 保存報告
    os.makedirs("/tmp/conversation_demo", exist_ok=True)
    report_path = "/tmp/conversation_demo/analysis_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"✓ 完整報告已保存到: {report_path}")


def main():
    """主程序"""
    print("\n" + "🧠 對話知識提取器 v1.0 - 示範程序")
    print("=" * 60)
    print("作者: MR.liou × Claude (empathetic.mirror)")
    print("=" * 60)
    
    try:
        demo_basic_usage()
        demo_attention_analysis()
        demo_logical_structure()
        demo_report_generation()
        
        print("\n" + "=" * 60)
        print("✅ 所有示範完成！")
        print("=" * 60)
        print("\n📁 輸出檔案位置: /tmp/conversation_demo/")
        print("  - demo.json (JSON 格式)")
        print("  - demo.md (Markdown 格式)")
        print("  - demo.txt (純文字格式)")
        print("  - demo.yaml (YAML 格式)")
        print("  - demo.csv (CSV 格式)")
        print("  - demo.html (HTML 格式)")
        print("  - demo.xml (XML 格式)")
        print("  - analysis_report.md (分析報告)")
        
    except Exception as e:
        print(f"\n❌ 執行錯誤: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
