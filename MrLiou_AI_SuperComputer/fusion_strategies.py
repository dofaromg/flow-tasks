"""
Fusion Strategies - AI Output Merging Functions
融合策略 - AI 輸出合併函數

Different strategies for merging multiple AI outputs:
- weighted_merge: Merge using particle weights
- consensus_merge: Use majority voting/consensus
- meta_ai_merge: Use another AI to merge outputs
- diff_merge: Keep common parts, highlight differences
- voting_merge: Democratic voting on answers (NEW)
- ensemble_merge: Statistical ensemble approach (NEW)
- confidence_weighted: Weight by confidence scores (NEW)
"""

from typing import List, Dict, Any, Optional
from difflib import SequenceMatcher
from collections import Counter
import re
import math


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


def voting_merge(outputs: List[Dict[str, Any]], min_agreement: float = 0.5) -> str:
    """
    Democratic voting approach - Enhanced computational method
    民主投票方法 - 增強的計算方法
    
    Uses similarity matching to group similar answers and vote
    """
    if not outputs:
        return ""
    
    if len(outputs) == 1:
        return outputs[0]["output"]
    
    result = "=== Voting Fusion Result ===\n\n"
    
    # Group similar outputs
    groups = []
    for output in outputs:
        text = output["output"]
        matched = False
        
        for group in groups:
            # Check similarity with group representative
            similarity = SequenceMatcher(None, text, group["representative"]).ratio()
            if similarity >= min_agreement:
                group["members"].append(output)
                group["votes"] += output.get("weight", 1.0)
                matched = True
                break
        
        if not matched:
            groups.append({
                "representative": text,
                "members": [output],
                "votes": output.get("weight", 1.0)
            })
    
    # Sort by votes
    groups.sort(key=lambda x: x["votes"], reverse=True)
    
    result += f"Total Groups: {len(groups)}\n\n"
    
    for i, group in enumerate(groups, 1):
        vote_percentage = (group["votes"] / len(outputs)) * 100
        result += f"Group {i} ({len(group['members'])} members, {vote_percentage:.1f}% votes):\n"
        result += f"{group['representative'][:300]}...\n"
        
        providers = ", ".join(m.get("provider", "Unknown") for m in group["members"])
        result += f"Providers: {providers}\n\n"
        result += "-" * 60 + "\n\n"
    
    result += "=== End Voting Fusion ==="
    return result


def ensemble_merge(outputs: List[Dict[str, Any]]) -> str:
    """
    Statistical ensemble approach - Enhanced computational method
    統計集成方法 - 增強的計算方法
    
    Combines outputs using statistical aggregation
    """
    if not outputs:
        return ""
    
    if len(outputs) == 1:
        return outputs[0]["output"]
    
    result = "=== Ensemble Fusion Result ===\n\n"
    
    # Compute statistics
    lengths = [len(o["output"]) for o in outputs]
    weights = [o.get("weight", 1.0) for o in outputs]
    
    avg_length = sum(lengths) / len(lengths)
    avg_weight = sum(weights) / len(weights)
    
    # Calculate diversity score
    diversity_scores = []
    for i, out1 in enumerate(outputs):
        for j, out2 in enumerate(outputs):
            if i < j:
                similarity = SequenceMatcher(None, out1["output"], out2["output"]).ratio()
                diversity_scores.append(1 - similarity)
    
    avg_diversity = sum(diversity_scores) / len(diversity_scores) if diversity_scores else 0
    
    result += f"Ensemble Statistics:\n"
    result += f"  • Number of models: {len(outputs)}\n"
    result += f"  • Average response length: {avg_length:.0f} chars\n"
    result += f"  • Average weight: {avg_weight:.2f}\n"
    result += f"  • Response diversity: {avg_diversity:.2%}\n\n"
    
    # Find most representative output (closest to average length)
    closest_idx = min(range(len(outputs)), key=lambda i: abs(lengths[i] - avg_length))
    representative = outputs[closest_idx]
    
    result += f"Representative Output (from {representative.get('provider', 'Unknown')}):\n"
    result += f"{representative['output']}\n\n"
    
    result += "=" * 60 + "\n\n"
    result += "All Ensemble Members:\n\n"
    
    for i, output in enumerate(outputs, 1):
        provider = output.get("provider", "Unknown")
        weight = output.get("weight", 1.0)
        result += f"{i}. {provider} (weight: {weight:.2f}):\n"
        result += f"{output['output'][:200]}...\n\n"
    
    result += "=== End Ensemble Fusion ==="
    return result


def confidence_weighted_merge(outputs: List[Dict[str, Any]]) -> str:
    """
    Confidence-weighted merge - Enhanced computational method
    置信度加權合併 - 增強的計算方法
    
    Uses confidence scores and adaptive weighting
    """
    # Configuration constant
    MAX_NORMALIZED_LENGTH = 1000  # Maximum length for normalization
    
    if not outputs:
        return ""
    
    if len(outputs) == 1:
        return outputs[0]["output"]
    
    result = "=== Confidence-Weighted Fusion Result ===\n\n"
    
    # Calculate confidence scores based on multiple factors
    for output in outputs:
        # Base confidence from weight
        base_conf = output.get("weight", 1.0)
        
        # Length factor (longer responses might be more detailed)
        length = len(output["output"])
        length_factor = min(1.0, length / MAX_NORMALIZED_LENGTH)  # Normalize to 1.0
        
        # Combined confidence
        confidence = (base_conf * 0.7 + length_factor * 0.3)
        output["_confidence"] = confidence
    
    # Sort by confidence
    sorted_outputs = sorted(outputs, key=lambda x: x["_confidence"], reverse=True)
    
    result += "Confidence Rankings:\n\n"
    
    for i, output in enumerate(sorted_outputs, 1):
        provider = output.get("provider", "Unknown")
        confidence = output["_confidence"]
        
        result += f"{i}. {provider} (confidence: {confidence:.2%})\n"
        result += f"{output['output']}\n\n"
        result += "-" * 60 + "\n\n"
    
    result += "=== End Confidence-Weighted Fusion ==="
    return result


def adaptive_fusion(outputs: List[Dict[str, Any]], convergence_threshold: float = 0.8) -> str:
    """
    Adaptive fusion with convergence detection - Enhanced computational method
    自適應融合與收斂檢測 - 增強的計算方法
    
    Dynamically selects the best fusion strategy based on output characteristics
    """
    if not outputs:
        return ""
    
    if len(outputs) == 1:
        return outputs[0]["output"]
    
    result = "=== Adaptive Fusion Result ===\n\n"
    
    # Analyze output characteristics
    similarities = []
    for i, out1 in enumerate(outputs):
        for j, out2 in enumerate(outputs):
            if i < j:
                sim = SequenceMatcher(None, out1["output"], out2["output"]).ratio()
                similarities.append(sim)
    
    avg_similarity = sum(similarities) / len(similarities) if similarities else 0
    
    result += f"Output Analysis:\n"
    result += f"  • Number of outputs: {len(outputs)}\n"
    result += f"  • Average similarity: {avg_similarity:.2%}\n"
    
    # Select strategy based on similarity
    if avg_similarity >= convergence_threshold:
        result += f"  • Strategy: CONSENSUS (high agreement)\n\n"
        strategy_result = consensus_merge(outputs)
    elif avg_similarity < 0.3:
        result += f"  • Strategy: VOTING (low agreement)\n\n"
        strategy_result = voting_merge(outputs)
    else:
        result += f"  • Strategy: ENSEMBLE (moderate agreement)\n\n"
        strategy_result = ensemble_merge(outputs)
    
    result += "=" * 60 + "\n\n"
    result += strategy_result
    
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
    "voting": voting_merge,  # NEW
    "ensemble": ensemble_merge,  # NEW
    "confidence": confidence_weighted_merge,  # NEW
    "adaptive": adaptive_fusion,  # NEW
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
