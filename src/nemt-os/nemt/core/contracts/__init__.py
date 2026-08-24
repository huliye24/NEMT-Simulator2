"""
NEMT 接口契约层

定义各层级间的标准接口，确保分形结构的自相似性。
"""

from .capsule_contracts import CapsuleMetadata, ICapsuleContract
from .pipeline_contracts import IPipelineContract, MarketPhase, PipelineInput, PipelineOutput

__all__ = [
    "ICapsuleContract",
    "CapsuleMetadata",
    "IPipelineContract",
    "PipelineInput",
    "PipelineOutput",
    "MarketPhase",
]
