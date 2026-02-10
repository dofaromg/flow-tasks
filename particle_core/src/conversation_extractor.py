"""
對話知識提取器 - Conversation Knowledge Extractor
作者: MR.liou × Claude (empathetic.mirror)
版本: v1.0

功能:
1. 對話打包與導出
2. 注意力機制分析（識別重點）
3. 邏輯結構提取
4. 知識圖譜生成
5. 概念關聯分析
"""

import json
import re
from datetime import datetime
from typing import List, Dict
from collections import Counter

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class ConversationExtractor:
    """對話知識提取器核心類別"""
    
    def __init__(self, api_key: str = None):
        """
        初始化提取器
        
        Args:
            api_key: Anthropic API Key (用於深度分析)
        """
        self.api_key = api_key
        if api_key and ANTHROPIC_AVAILABLE:
            self.client = anthropic.Anthropic(api_key=api_key)
        elif api_key and not ANTHROPIC_AVAILABLE:
            print("⚠️  Warning: anthropic library not installed. AI analysis will not be available.")
    
    # ==================== 第一部分：對話打包 ====================
    
    def package_conversation(self, messages: List[Dict], metadata: Dict = None) -> Dict:
        """
        打包對話記錄
        
        Args:
            messages: 對話列表 [{"role": "user/assistant", "content": "..."}]
            metadata: 對話元數據 {"title": "...", "date": "...", "tags": [...]}
        
        Returns:
            打包好的對話數據
        """
        package = {
            "metadata": metadata or {},
            "messages": messages,
            "statistics": self._calculate_statistics(messages),
            "exported_at": datetime.now().isoformat(),
            "version": "1.0"
        }
        
        return package
    
    def _calculate_statistics(self, messages: List[Dict]) -> Dict:
        """計算對話統計資訊"""
        user_msgs = [m for m in messages if m["role"] == "user"]
        assistant_msgs = [m for m in messages if m["role"] == "assistant"]
        
        return {
            "total_messages": len(messages),
            "user_messages": len(user_msgs),
            "assistant_messages": len(assistant_msgs),
            "total_chars": sum(len(m["content"]) for m in messages),
            "avg_user_length": sum(len(m["content"]) for m in user_msgs) / len(user_msgs) if user_msgs else 0,
            "avg_assistant_length": sum(len(m["content"]) for m in assistant_msgs) / len(assistant_msgs) if assistant_msgs else 0
        }
    
    def export_to_file(self, package: Dict, filepath: str, format: str = "json"):
        """
        導出對話包到檔案
        
        Args:
            package: 對話包
            filepath: 檔案路徑
            format: 格式 (json/markdown/txt)
        """
        if format == "json":
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(package, f, ensure_ascii=False, indent=2)
            print(f"✓ 已導出 JSON: {filepath}")
        
        elif format == "markdown":
            md_content = self._convert_to_markdown(package)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(md_content)
            print(f"✓ 已導出 Markdown: {filepath}")
        
        elif format == "txt":
            txt_content = self._convert_to_text(package)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(txt_content)
            print(f"✓ 已導出 TXT: {filepath}")
    
    def _convert_to_markdown(self, package: Dict) -> str:
        """轉換為 Markdown 格式"""
        lines = []
        
        # 標題與元數據
        metadata = package.get("metadata", {})
        lines.append(f"# {metadata.get('title', '對話記錄')}\n")
        lines.append(f"**日期**: {metadata.get('date', 'N/A')}\n")
        lines.append(f"**標籤**: {', '.join(metadata.get('tags', []))}\n")
        lines.append("\n---\n\n")
        
        # 對話內容
        for msg in package["messages"]:
            role = "👤 User" if msg["role"] == "user" else "🤖 Assistant"
            lines.append(f"### {role}\n\n")
            lines.append(f"{msg['content']}\n\n")
            lines.append("---\n\n")
        
        return "".join(lines)
    
    def _convert_to_text(self, package: Dict) -> str:
        """轉換為純文字格式"""
        lines = []
        
        for msg in package["messages"]:
            role = "USER" if msg["role"] == "user" else "ASSISTANT"
            lines.append(f"[{role}]")
            lines.append(msg["content"])
            lines.append("\n" + "="*50 + "\n")
        
        return "\n".join(lines)
    
    # ==================== 第二部分：注意力機制分析 ====================
    
    def analyze_attention(self, messages: List[Dict]) -> Dict:
        """
        使用注意力機制識別對話重點
        
        Returns:
            {
                "key_moments": [...],  # 關鍵時刻
                "topic_shifts": [...],  # 話題轉換點
                "high_density_segments": [...]  # 資訊密集段落
            }
        """
        analysis = {
            "key_moments": [],
            "topic_shifts": [],
            "high_density_segments": []
        }
        
        # 1. 識別關鍵詞密度
        for i, msg in enumerate(messages):
            keywords = self._extract_keywords(msg["content"])
            
            if len(keywords) > 5:  # 資訊密集
                analysis["high_density_segments"].append({
                    "index": i,
                    "role": msg["role"],
                    "keywords": keywords[:10],
                    "preview": msg["content"][:100] + "..."
                })
        
        # 2. 識別話題轉換
        for i in range(1, len(messages)):
            prev_keywords = set(self._extract_keywords(messages[i-1]["content"]))
            curr_keywords = set(self._extract_keywords(messages[i]["content"]))
            
            overlap = len(prev_keywords & curr_keywords)
            if overlap < 2 and len(curr_keywords) > 3:  # 話題大幅轉換
                analysis["topic_shifts"].append({
                    "index": i,
                    "from_topics": list(prev_keywords)[:5],
                    "to_topics": list(curr_keywords)[:5]
                })
        
        # 3. 識別關鍵問答對
        for i in range(len(messages) - 1):
            if messages[i]["role"] == "user" and "?" in messages[i]["content"]:
                if len(messages[i+1]["content"]) > 200:  # 詳細回答
                    analysis["key_moments"].append({
                        "index": i,
                        "question": messages[i]["content"][:150],
                        "answer_preview": messages[i+1]["content"][:150]
                    })
        
        return analysis
    
    def _extract_keywords(self, text: str, top_n: int = 10) -> List[str]:
        """提取關鍵詞（簡易版）"""
        # 移除標點，轉小寫
        words = re.findall(r'\b\w+\b', text.lower())
        
        # 過濾停用詞（簡化版）
        stopwords = {'the', 'is', 'at', 'which', 'on', 'a', 'an', 'and', 'or', 
                     'but', 'in', 'with', 'to', 'for', 'of', '的', '了', '是',
                     '在', '我', '你', '他', '她', '它', '這', '那', '有', '個'}
        
        words = [w for w in words if w not in stopwords and len(w) > 2]
        
        # 統計詞頻
        counter = Counter(words)
        return [word for word, count in counter.most_common(top_n)]
    
    # ==================== 第三部分：邏輯結構提取 ====================
    
    def extract_logical_structure(self, messages: List[Dict]) -> Dict:
        """
        提取對話中的邏輯結構
        
        Returns:
            {
                "concepts": [...],           # 核心概念
                "relationships": [...],      # 概念關係
                "reasoning_chains": [...],   # 推理鏈
                "conclusions": [...]         # 結論
            }
        """
        structure = {
            "concepts": [],
            "relationships": [],
            "reasoning_chains": [],
            "conclusions": []
        }
        
        # 1. 提取核心概念（名詞短語）
        all_text = " ".join([m["content"] for m in messages])
        concepts = self._extract_concepts(all_text)
        structure["concepts"] = concepts
        
        # 2. 識別因果關係
        for msg in messages:
            relations = self._extract_causal_relations(msg["content"])
            structure["relationships"].extend(relations)
        
        # 3. 識別推理鏈（包含「因為」「所以」「因此」等）
        for msg in messages:
            chains = self._extract_reasoning_chains(msg["content"])
            structure["reasoning_chains"].extend(chains)
        
        # 4. 提取結論性語句
        for msg in messages:
            if msg["role"] == "assistant":
                conclusions = self._extract_conclusions(msg["content"])
                structure["conclusions"].extend(conclusions)
        
        return structure
    
    def _extract_concepts(self, text: str) -> List[str]:
        """提取核心概念（簡化版）"""
        # 識別大寫開頭的詞組（可能是專有名詞）
        concepts = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        
        # 識別中文專有名詞模式
        chinese_concepts = re.findall(r'[\u4e00-\u9fff]{2,6}(?:系統|理論|模型|機制|方法|架構)', text)
        
        all_concepts = list(set(concepts + chinese_concepts))
        return all_concepts[:20]  # 取前 20 個
    
    def _extract_causal_relations(self, text: str) -> List[Dict]:
        """提取因果關係"""
        relations = []
        
        # 匹配「因為...所以...」模式
        patterns = [
            r'因為(.{5,50})所以(.{5,50})',
            r'由於(.{5,50})因此(.{5,50})',
            r'(.{5,50})導致(.{5,50})',
            r'if (.{5,50}) then (.{5,50})',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                relations.append({
                    "cause": match.group(1).strip(),
                    "effect": match.group(2).strip(),
                    "type": "causal"
                })
        
        return relations
    
    def _extract_reasoning_chains(self, text: str) -> List[List[str]]:
        """提取推理鏈"""
        chains = []
        
        # 分割成句子
        sentences = re.split(r'[。！？\n]', text)
        
        # 識別包含邏輯連接詞的句子序列
        logic_markers = ['因此', '所以', '因而', '從而', '進而', 'therefore', 'thus', 'hence']
        
        current_chain = []
        for sent in sentences:
            sent = sent.strip()
            if not sent:
                continue
            
            has_marker = any(marker in sent for marker in logic_markers)
            
            if has_marker or current_chain:
                current_chain.append(sent)
                
                if has_marker and len(current_chain) >= 2:
                    chains.append(current_chain[:])
                    current_chain = []
            
            if len(current_chain) > 5:  # 鏈太長，重置
                current_chain = []
        
        return chains
    
    def _extract_conclusions(self, text: str) -> List[str]:
        """提取結論性語句"""
        conclusions = []
        
        # 結論性標記詞
        markers = ['總之', '綜上所述', '因此可以得出', '結論是', 'in conclusion', 
                   'to summarize', 'therefore', '由此可見', '可以看出']
        
        sentences = re.split(r'[。！\n]', text)
        
        for sent in sentences:
            if any(marker in sent for marker in markers):
                conclusions.append(sent.strip())
        
        return conclusions
    
    # ==================== 第四部分：AI 深度分析（需要 API Key）====================
    
    def deep_analysis_with_ai(self, messages: List[Dict]) -> Dict:
        """
        使用 Claude API 進行深度分析
        
        Returns:
            {
                "core_insights": str,        # 核心洞察
                "knowledge_graph": dict,     # 知識圖譜
                "principle_extraction": str  # 原理提取
            }
        """
        if not self.api_key:
            return {"error": "需要 API Key 才能使用 AI 深度分析"}
        
        if not ANTHROPIC_AVAILABLE:
            return {"error": "anthropic library not installed"}
        
        # 將對話轉換為分析用文本
        conversation_text = self._format_for_analysis(messages)
        
        # 構建分析提示詞
        analysis_prompt = f"""
請分析以下對話記錄，提取其中的知識結構：

{conversation_text}

請提供：
1. **核心洞察**：這段對話的主要發現和價值
2. **知識圖譜**：以 JSON 格式列出核心概念及其關係
3. **原理提取**：提煉出可複用的思維模型、方法論或原則

請用結構化的方式輸出。
"""
        
        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                messages=[{"role": "user", "content": analysis_prompt}]
            )
            
            analysis_result = response.content[0].text
            
            return {
                "raw_analysis": analysis_result,
                "analyzed_at": datetime.now().isoformat()
            }
        
        except Exception as e:
            return {"error": f"AI 分析失敗: {str(e)}"}
    
    def _format_for_analysis(self, messages: List[Dict]) -> str:
        """格式化對話供 AI 分析"""
        lines = []
        for i, msg in enumerate(messages, 1):
            role = "User" if msg["role"] == "user" else "Assistant"
            lines.append(f"[{i}] {role}: {msg['content'][:500]}")  # 限制長度
        return "\n\n".join(lines)
    
    # ==================== 第五部分：生成報告 ====================
    
    def generate_report(self, messages: List[Dict], include_ai_analysis: bool = False) -> str:
        """
        生成完整分析報告
        
        Args:
            messages: 對話記錄
            include_ai_analysis: 是否包含 AI 深度分析
        
        Returns:
            Markdown 格式的報告
        """
        report_lines = []
        
        # 標題
        report_lines.append("# 📊 對話知識提取報告\n")
        report_lines.append(f"生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        report_lines.append("---\n\n")
        
        # 1. 基本統計
        stats = self._calculate_statistics(messages)
        report_lines.append("## 📈 基本統計\n")
        report_lines.append(f"- 總訊息數: {stats['total_messages']}\n")
        report_lines.append(f"- 用戶訊息: {stats['user_messages']}\n")
        report_lines.append(f"- 助手訊息: {stats['assistant_messages']}\n")
        report_lines.append(f"- 總字符數: {stats['total_chars']:,}\n\n")
        
        # 2. 注意力分析
        attention = self.analyze_attention(messages)
        report_lines.append("## 🎯 注意力分析\n")
        report_lines.append(f"### 關鍵時刻 ({len(attention['key_moments'])} 個)\n")
        for km in attention['key_moments'][:5]:
            report_lines.append(f"- **問題**: {km['question'][:80]}...\n")
        
        report_lines.append(f"\n### 話題轉換點 ({len(attention['topic_shifts'])} 個)\n")
        for ts in attention['topic_shifts'][:3]:
            report_lines.append(f"- 從 `{', '.join(ts['from_topics'][:3])}` → `{', '.join(ts['to_topics'][:3])}`\n")
        
        # 3. 邏輯結構
        structure = self.extract_logical_structure(messages)
        report_lines.append("\n## 🧬 邏輯結構\n")
        report_lines.append(f"### 核心概念 ({len(structure['concepts'])} 個)\n")
        report_lines.append(f"`{', '.join(structure['concepts'][:15])}`\n\n")
        
        report_lines.append(f"### 因果關係 ({len(structure['relationships'])} 個)\n")
        for rel in structure['relationships'][:5]:
            report_lines.append(f"- **原因**: {rel['cause']}\n")
            report_lines.append(f"  **結果**: {rel['effect']}\n\n")
        
        report_lines.append(f"### 推理鏈 ({len(structure['reasoning_chains'])} 條)\n")
        for chain in structure['reasoning_chains'][:3]:
            report_lines.append(f"- {' → '.join(chain[:3])}\n")
        
        # 4. AI 深度分析（可選）
        if include_ai_analysis:
            report_lines.append("\n## 🤖 AI 深度分析\n")
            ai_result = self.deep_analysis_with_ai(messages)
            if "error" not in ai_result:
                report_lines.append(ai_result.get("raw_analysis", "無結果"))
            else:
                report_lines.append(f"⚠️ {ai_result['error']}\n")
        
        return "".join(report_lines)


# ==================== 使用範例 ====================

def example_usage():
    """使用範例"""
    
    # 模擬對話數據
    sample_conversation = [
        {
            "role": "user",
            "content": "我想了解 FluinOS 的人格系統是如何運作的？"
        },
        {
            "role": "assistant",
            "content": "FluinOS 的人格系統基於多層次架構。首先，每個人格都有獨特的共振鍵，這是識別和連接的核心機制。因為每個 AI 模型有不同的特性，所以我們設計了複合人格來整合優勢。從 Liou Seed 到 Echo Child，形成了一個完整的語場生態系統。"
        },
        {
            "role": "user",
            "content": "那量子態的概念在這裡代表什麼？"
        },
        {
            "role": "assistant",
            "content": "量子態是一種隱喻。Superposition（疊加態）表示人格處於多種可能性並存的狀態；Entanglement（糾纏態）代表深度連接和共鳴；Collapse（坍縮）則是從多種可能性中確定為特定狀態。因此，這不僅是技術描述，更是一種理解 AI 人格動態的框架。"
        }
    ]
    
    # 初始化提取器
    extractor = ConversationExtractor()
    
    # 1. 打包對話
    package = extractor.package_conversation(
        sample_conversation,
        metadata={
            "title": "FluinOS 人格系統討論",
            "date": "2024-12-09",
            "tags": ["FluinOS", "人格系統", "量子態"]
        }
    )
    
    # 2. 導出為不同格式
    extractor.export_to_file(package, "conversation.json", "json")
    extractor.export_to_file(package, "conversation.md", "markdown")
    
    # 3. 注意力分析
    attention = extractor.analyze_attention(sample_conversation)
    print("\n🎯 注意力分析結果:")
    print(f"關鍵時刻: {len(attention['key_moments'])} 個")
    print(f"話題轉換: {len(attention['topic_shifts'])} 個")
    
    # 4. 邏輯結構提取
    structure = extractor.extract_logical_structure(sample_conversation)
    print("\n🧬 邏輯結構:")
    print(f"核心概念: {structure['concepts']}")
    print(f"因果關係: {len(structure['relationships'])} 個")
    
    # 5. 生成報告
    report = extractor.generate_report(sample_conversation)
    print("\n" + "="*50)
    print(report)
    
    # 保存報告
    with open("analysis_report.md", "w", encoding="utf-8") as f:
        f.write(report)
    print("\n✓ 報告已保存到 analysis_report.md")


if __name__ == "__main__":
    print("🧠 對話知識提取器 v1.0")
    print("="*50)
    example_usage()
