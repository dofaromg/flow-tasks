"""
Fusion Strategies - AI Output Merging Functions
融合策略 - AI 輸出合併函數

Different strategies for merging multiple AI outputs:
- weighted_merge: Merge using particle weights
- consensus_merge: Use majority voting/consensus
- meta_ai_merge: Use another AI to merge outputs
- diff_merge: Keep common parts, highlight differences
"""

from typing import List, Dict, Any
from difflib import SequenceMatcher
from collections import Counter
import re


def weighted_merge(outputs: List[Dict[str, Any]]) -> str:
    """
    Merge outputs using weights
    使用權重合併輸出
    
    Args:
        outputs: List of output dicts with 'output', 'weight', 'provider'
    
    Returns:
        Merged output string with weight annotations
    """
    if not outputs:
        return ""
    
    if len(outputs) == 1:
        return outputs[0]["output"]
    
    total_weight = sum(o.get("weight", 1.0) for o in outputs)
    
    result = "=== Weighted Fusion Result ===\n\n"
    
    for output in outputs:
        weight = output.get("weight", 1.0)
        percentage = (weight / total_weight) * 100
        provider = output.get("provider", "Unknown")
        model = output.get("model", "")
        
        result += f"[{provider}/{model} - Weight: {percentage:.1f}%]\n"
        result += f"{output['output']}\n\n"
        result += "-" * 60 + "\n\n"
    
    result += "=== End Weighted Fusion ==="
    return result


def consensus_merge(outputs: List[Dict[str, Any]]) -> str:
    """
    Use majority voting/consensus
    使用多數投票/共識
    
    Extracts common themes and creates consensus view
    """
    if not outputs:
        return ""
    
    if len(outputs) == 1:
        return outputs[0]["output"]
    
    result = "=== Consensus Fusion Result ===\n\n"
    
    # Extract key phrases from each output (simple tokenization)
    all_phrases = []
    for output in outputs:
        text = output["output"]
        # Simple extraction: sentences
        sentences = re.split(r'[.!?]+', text)
        all_phrases.extend([s.strip() for s in sentences if s.strip()])
    
    # Find common themes (simplified)
    result += "Common Themes:\n"
    if all_phrases:
        # Count phrase frequency
        phrase_counts = Counter(all_phrases)
        common = phrase_counts.most_common(3)
        for phrase, count in common:
            if count > 1:
                result += f"  • {phrase} (mentioned {count} times)\n"
    
    result += "\n" + "=" * 60 + "\n\n"
    result += "Individual Perspectives:\n\n"
    
    for i, output in enumerate(outputs, 1):
        provider = output.get("provider", "Unknown")
        result += f"{i}. {provider}: {output['output'][:200]}...\n\n"
    
    result += "=== End Consensus Fusion ==="
    return result


def meta_ai_merge(outputs: List[Dict[str, Any]], meta_provider: Any = None) -> str:
    """
    Use another AI to merge the outputs
    使用另一個 AI 來合併輸出
    
    Args:
        outputs: List of AI outputs
        meta_provider: AI provider to use for merging (optional)
    
    Returns:
        Merged output from meta-AI analysis
    """
    if not outputs:
        return ""
    
    if len(outputs) == 1:
        return outputs[0]["output"]
    
    # Build prompt for meta-AI
    prompt = "Synthesize these responses into a coherent answer:\n\n"
    
    for i, output in enumerate(outputs, 1):
        provider = output.get("provider", "Unknown")
        prompt += f"{i}. From {provider}:\n{output['output']}\n\n"
    
    # If meta_provider available, use it; otherwise return structured view
    if meta_provider:
        try:
            meta_result = meta_provider.generate(prompt)
            return f"=== Meta-AI Synthesis ===\n\n{meta_result}\n\n=== End Meta-AI Synthesis ==="
        except:
            pass
    
    # Fallback: structured presentation
    result = "=== Meta-Synthesis (Structured) ===\n\n"
    result += "Sources to synthesize:\n\n"
    
    for i, output in enumerate(outputs, 1):
        provider = output.get("provider", "Unknown")
        result += f"{i}. {provider}:\n{output['output']}\n\n"
        result += "-" * 60 + "\n\n"
    
    result += "Note: For AI-powered synthesis, provide a meta_provider.\n"
    result += "=== End Meta-Synthesis ==="
    return result


def diff_merge(outputs: List[Dict[str, Any]]) -> str:
    """
    Keep common parts, highlight differences
    保留共同部分，突出差異
    
    Uses sequence matching to find common and unique parts
    """
    if not outputs:
        return ""
    
    if len(outputs) == 1:
        return outputs[0]["output"]
    
    result = "=== Differential Fusion Result ===\n\n"
    
    # Compare outputs pairwise
    if len(outputs) >= 2:
        text1 = outputs[0]["output"]
        text2 = outputs[1]["output"]
        
        matcher = SequenceMatcher(None, text1, text2)
        similarity = matcher.ratio()
        
        result += f"Similarity: {similarity * 100:.1f}%\n\n"
        
        # Extract matching blocks
        result += "Common Elements:\n"
        for block in matcher.get_matching_blocks():
            if block.size > 20:  # Only significant matches
                common_text = text1[block.a:block.a + block.size]
                result += f"  • {common_text.strip()[:100]}...\n"
        
        result += "\n" + "=" * 60 + "\n\n"
    
    result += "Unique Perspectives:\n\n"
    
    for i, output in enumerate(outputs, 1):
        provider = output.get("provider", "Unknown")
        result += f"{i}. {provider}:\n{output['output']}\n\n"
        result += "-" * 60 + "\n\n"
    
    result += "=== End Differential Fusion ==="
    return result


def simple_concatenate(outputs: List[Dict[str, Any]]) -> str:
    """
    Simple concatenation with provider labels
    簡單串聯並標記提供者
    """
    if not outputs:
        return ""
    
    result = "=== Concatenated Fusion Result ===\n\n"
    
    for output in outputs:
        provider = output.get("provider", "Unknown")
        model = output.get("model", "")
        role = output.get("role", "")
        
        result += f"[{provider}/{model}"
        if role:
            result += f" - {role}"
        result += "]\n"
        result += f"{output['output']}\n\n"
        result += "=" * 60 + "\n\n"
    
    result += "=== End Concatenated Fusion ==="
    return result


def extract_best(outputs: List[Dict[str, Any]], criterion: str = "length") -> str:
    """
    Extract the "best" output based on a criterion
    根據標準提取"最佳"輸出
    
    Args:
        outputs: List of outputs
        criterion: 'length', 'weight', or 'first'
    """
    if not outputs:
        return ""
    
    if len(outputs) == 1:
        return outputs[0]["output"]
    
    if criterion == "length":
        best = max(outputs, key=lambda x: len(x["output"]))
    elif criterion == "weight":
        best = max(outputs, key=lambda x: x.get("weight", 0))
    else:  # first
        best = outputs[0]
    
    provider = best.get("provider", "Unknown")
    result = f"=== Best Output (by {criterion}) from {provider} ===\n\n"
    result += best["output"]
    result += f"\n\n=== End Best Output ==="
    return result


# Strategy registry
STRATEGIES = {
    "weighted": weighted_merge,
    "consensus": consensus_merge,
    "meta_ai": meta_ai_merge,
    "diff": diff_merge,
    "concatenate": simple_concatenate,
    "best_length": lambda x: extract_best(x, "length"),
    "best_weight": lambda x: extract_best(x, "weight"),
}


def apply_strategy(strategy_name: str, outputs: List[Dict[str, Any]], **kwargs) -> str:
    """
    Apply a named merge strategy
    應用命名合併策略
    
    Args:
        strategy_name: Name of strategy from STRATEGIES
        outputs: List of AI outputs
        **kwargs: Additional arguments for specific strategies
    
    Returns:
        Merged output string
    """
    strategy = STRATEGIES.get(strategy_name, simple_concatenate)
    
    if strategy_name == "meta_ai" and "meta_provider" in kwargs:
        return strategy(outputs, meta_provider=kwargs["meta_provider"])
    
    return strategy(outputs)


if __name__ == "__main__":
    # Demo usage
    print("=== Fusion Strategies Demo ===\n")
    
    # Sample outputs
    test_outputs = [
        {
            "provider": "openai",
            "model": "gpt-4",
            "output": "Quantum entanglement is a phenomenon where particles become correlated.",
            "weight": 0.4
        },
        {
            "provider": "claude",
            "model": "claude-3",
            "output": "Quantum entanglement represents a fundamental connection between particles.",
            "weight": 0.4
        },
        {
            "provider": "gemini",
            "model": "gemini-pro",
            "output": "Entanglement shows how quantum particles share states instantaneously.",
            "weight": 0.2
        }
    ]
    
    print("1. Weighted Merge:")
    print(weighted_merge(test_outputs))
    print("\n" + "=" * 80 + "\n")
    
    print("2. Consensus Merge:")
    print(consensus_merge(test_outputs))
    print("\n" + "=" * 80 + "\n")
    
    print("3. Diff Merge:")
    print(diff_merge(test_outputs))
    print("\n")
