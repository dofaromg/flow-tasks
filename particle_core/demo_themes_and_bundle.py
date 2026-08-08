"""
對話知識提取器 - 主題與套件生成示範
Demonstration of Theme Variations and Website Bundle Generation

展示新功能:
1. 可自訂調色盤主題
2. 批次導出多種格式
3. 生成完整網站套件
"""

import os
import sys

# 將 particle_core/src 加入路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from conversation_extractor import ConversationExtractor


def demo_themes():
    """示範不同主題效果"""
    print("\n" + "=" * 70)
    print("🎨 示範 1：調色盤主題變化")
    print("=" * 70)
    
    # 準備對話
    conversation = [
        {
            "role": "user",
            "content": "什麼是對話知識提取器的新功能？"
        },
        {
            "role": "assistant",
            "content": "對話知識提取器現在支援多種調色盤主題！包括：預設、海洋、日落、夜晚、森林、極簡等 6 種主題。每個主題都有精心設計的配色方案，讓你的對話記錄更加美觀。"
        },
        {
            "role": "user",
            "content": "還有其他新功能嗎？"
        },
        {
            "role": "assistant",
            "content": "是的！新增了批次導出功能和網站套件生成功能。你可以一次導出所有格式，或者生成包含多個主題的完整網站，非常適合展示和分享你的對話記錄。"
        }
    ]
    
    # 測試不同主題
    themes = ["default", "ocean", "sunset", "night", "forest", "minimal"]
    output_dir = "/tmp/theme_demo"
    os.makedirs(output_dir, exist_ok=True)
    
    for theme in themes:
        extractor = ConversationExtractor(theme=theme)
        package = extractor.package_conversation(
            conversation,
            metadata={
                "title": f"主題示範 - {theme.capitalize()}",
                "date": "2026-01-09",
                "tags": ["主題", theme]
            }
        )
        
        filepath = os.path.join(output_dir, f"demo_{theme}.html")
        extractor.export_to_file(package, filepath, "html")
    
    print(f"\n✓ 已生成 {len(themes)} 個主題變化")
    print(f"📁 檔案位置: {output_dir}/demo_*.html")


def demo_batch_export():
    """示範批次導出功能"""
    print("\n" + "=" * 70)
    print("📦 示範 2：批次導出多種格式")
    print("=" * 70)
    
    conversation = [
        {
            "role": "user",
            "content": "批次導出有什麼好處？"
        },
        {
            "role": "assistant",
            "content": "批次導出讓你可以一次生成所有格式的檔案，不需要逐一調用。這樣可以節省時間，確保所有格式的內容保持一致。特別適合需要在不同場景下使用不同格式的情況。"
        }
    ]
    
    extractor = ConversationExtractor(theme="ocean")
    package = extractor.package_conversation(
        conversation,
        metadata={
            "title": "批次導出示範",
            "date": "2026-01-09",
            "tags": ["批次", "多格式"]
        }
    )
    
    # 批次導出所有格式
    base_path = "/tmp/batch_demo/conversation"
    os.makedirs("/tmp/batch_demo", exist_ok=True)
    
    exported = extractor.export_batch(package, base_path)
    
    print(f"\n✓ 成功導出 {len(exported)} 個檔案:")
    for filepath in exported:
        print(f"  • {os.path.basename(filepath)}")


def demo_website_bundle():
    """示範網站套件生成"""
    print("\n" + "=" * 70)
    print("🌐 示範 3：生成完整網站套件")
    print("=" * 70)
    
    conversation = [
        {
            "role": "user",
            "content": "網站套件包含什麼？"
        },
        {
            "role": "assistant",
            "content": "網站套件包含：\n1. 多個主題的 HTML 頁面（所有 6 種主題）\n2. 所有格式的數據檔案（JSON, YAML, CSV, XML, Markdown, TXT）\n3. 一個美觀的索引頁面，方便瀏覽和下載"
        },
        {
            "role": "user",
            "content": "這有什麼實際用途？"
        },
        {
            "role": "assistant",
            "content": "非常適合：\n• 分享對話記錄給團隊成員\n• 建立知識庫或文檔站點\n• 展示 AI 對話成果\n• 多格式備份重要對話\n每個人可以選擇自己喜歡的主題和格式查看。"
        }
    ]
    
    extractor = ConversationExtractor()
    package = extractor.package_conversation(
        conversation,
        metadata={
            "title": "對話知識提取器 - 功能展示",
            "date": "2026-01-09",
            "tags": ["網站套件", "多主題", "完整功能"]
        }
    )
    
    # 生成完整網站套件
    output_dir = "/tmp/website_bundle"
    result = extractor.generate_website_bundle(package, output_dir)
    
    print(f"\n📊 生成內容總覽:")
    print(f"  • HTML 主題頁面: {len(result['html_files'])} 個")
    print(f"  • 數據檔案: {len(result['data_files'])} 個")
    print(f"  • 索引頁面: 1 個")
    print(f"\n💡 提示: 在瀏覽器中打開 {output_dir}/index.html 查看完整網站")


def demo_custom_palette():
    """示範自訂調色盤"""
    print("\n" + "=" * 70)
    print("🎨 示範 4：自訂調色盤")
    print("=" * 70)
    
    conversation = [
        {
            "role": "user",
            "content": "我可以自訂顏色嗎？"
        },
        {
            "role": "assistant",
            "content": "當然可以！你可以傳入自訂的調色盤字典，完全控制所有顏色。這樣可以配合你的品牌色彩或個人喜好。"
        }
    ]
    
    # 自訂調色盤（粉紅主題）
    custom_palette = {
        "bg_body": "#fce4ec",
        "bg_container": "white",
        "bg_metadata": "#f8bbd0",
        "bg_user": "#f48fb1",
        "bg_assistant": "#ce93d8",
        "bg_stats": "#fff9c4",
        "border_title": "#c2185b",
        "border_user": "#e91e63",
        "border_assistant": "#9c27b0",
        "text_primary": "#880e4f",
        "text_secondary": "#ad1457"
    }
    
    extractor = ConversationExtractor()
    package = extractor.package_conversation(
        conversation,
        metadata={
            "title": "自訂粉紅主題",
            "date": "2026-01-09",
            "tags": ["自訂", "粉紅"]
        }
    )
    
    # 使用自訂調色盤
    html_content = extractor._convert_to_html(package, custom_palette=custom_palette)
    
    output_path = "/tmp/custom_palette_demo.html"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n✓ 已生成自訂主題 HTML")
    print(f"📁 檔案位置: {output_path}")


def main():
    """主程序"""
    print("\n" + "🎨 對話知識提取器 v2.0 - 主題與套件生成示範")
    print("=" * 70)
    print("新功能:")
    print("  • 6 種預設主題調色盤")
    print("  • 批次導出多種格式")
    print("  • 完整網站套件生成")
    print("  • 自訂調色盤支援")
    print("=" * 70)
    
    try:
        # 執行所有示範
        demo_themes()
        demo_batch_export()
        demo_website_bundle()
        demo_custom_palette()
        
        print("\n" + "=" * 70)
        print("✅ 所有示範完成！")
        print("=" * 70)
        print("\n📁 生成的檔案:")
        print("  • 主題示範: /tmp/theme_demo/")
        print("  • 批次導出: /tmp/batch_demo/")
        print("  • 網站套件: /tmp/website_bundle/")
        print("  • 自訂主題: /tmp/custom_palette_demo.html")
        print("\n💡 提示: 使用瀏覽器打開 HTML 檔案查看效果")
        
    except Exception as e:
        print(f"\n❌ 執行錯誤: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
