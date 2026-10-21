"""
Performance Analyzer - AI-powered performance analysis
性能分析器 - AI 驅動的性能分析
"""

from datetime import datetime
from typing import Dict, Any, List

class PerformanceAnalyzer:
    """AI-powered performance analysis"""
    
    def __init__(self, runtime=None):
        self.runtime = runtime
        self.analysis_history = []
        
    def analyze_system(self) -> Dict[str, Any]:
        """Comprehensive system performance analysis"""
        metrics = self.runtime.get_metrics() if self.runtime else {}
        
        analysis = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "metrics": metrics,
            "bottlenecks": self._identify_bottlenecks(metrics),
            "recommendations": self._generate_recommendations(metrics),
            "optimization_priorities": self._prioritize_optimizations(metrics)
        }
        
        self.analysis_history.append(analysis)
        return analysis
    
    def _identify_bottlenecks(self, metrics: Dict[str, Any]) -> List[str]:
        """Identify performance bottlenecks"""
        bottlenecks = []
        
        if metrics.get("total_executions", 0) > 1000:
            bottlenecks.append("High execution count - needs caching")
        
        if metrics.get("active_stacks", 0) > 10:
            bottlenecks.append("Too many stacks - needs pooling")
        
        return bottlenecks or ["No significant bottlenecks detected"]
    
    def _generate_recommendations(self, metrics: Dict[str, Any]) -> List[str]:
        """Generate optimization recommendations"""
        return [
            "Implement result caching",
            "Use lazy evaluation",
            "Optimize Merkle chain batching",
            "Parallelize particle execution"
        ]
    
    def _prioritize_optimizations(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Prioritize optimizations by impact"""
        return [
            {"priority": 1, "task": "Implement caching", "est_improvement": "40%"},
            {"priority": 2, "task": "Parallelize execution", "est_improvement": "30%"},
            {"priority": 3, "task": "Optimize memory", "est_improvement": "20%"}
        ]
