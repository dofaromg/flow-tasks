#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MrliouaAI mrl_ai_os - 去重 / 蒸餾 / 回收（重組）正式生產管道模板

提供可重用的生產模板設定，對齊 conversation_extractor 的
process_external_analysis_pipeline 既有能力。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol


class ExternalAnalysisExtractor(Protocol):
    """Minimal protocol required by run_with_template()."""

    def process_external_analysis_pipeline(
        self,
        source: Any,
        source_type: str = "auto",
        operations: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        trust_level: str = "medium",
    ) -> Dict[str, Any]:
        ...


@dataclass(frozen=True)
class PipelineTemplate:
    """Production pipeline template settings / 正式生產管道模板設定。"""

    product_vendor: str = "MrliouaAI"
    product_name: str = "mrl_ai_os"
    environment: str = "production"
    trust_level: str = "high"
    operations: List[str] = field(
        default_factory=lambda: ["ingest", "deduplicate", "decompose", "distill", "recompose"]
    )

    def to_metadata(self, branch: str, extra_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        metadata = {
            "vendor": self.product_vendor,
            "product": self.product_name,
            "environment": self.environment,
            "branch": branch,
            "pipeline_template": "dedup-distill-recycle-v1",
        }
        if extra_metadata:
            metadata.update(extra_metadata)
        return metadata


def build_production_template() -> PipelineTemplate:
    """Return default MrliouaAI mrl_ai_os production template."""
    return PipelineTemplate()


def run_with_template(
    extractor: ExternalAnalysisExtractor,
    source: Any,
    *,
    branch: str = "main",
    source_type: str = "auto",
    trust_level: Optional[str] = None,
    extra_metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Execute external analysis pipeline with production template metadata.

    extractor 需提供 process_external_analysis_pipeline(...)。
    """

    template = build_production_template()
    return extractor.process_external_analysis_pipeline(
        source=source,
        source_type=source_type,
        operations=template.operations,
        metadata=template.to_metadata(branch=branch, extra_metadata=extra_metadata),
        trust_level=trust_level or template.trust_level,
    )
