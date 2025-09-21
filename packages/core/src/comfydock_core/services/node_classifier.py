"""Node classification service for workflow analysis."""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import TYPE_CHECKING

from ..logging.logging_config import get_logger

if TYPE_CHECKING:
    from ..configs.model_config import ModelConfig
    from ..models.workflow import Workflow, WorkflowNode

logger = get_logger(__name__)

# Cache for builtin nodes (loaded once)
_BUILTIN_NODES: set[str] | None = None

@dataclass
class NodeClassifierResult:
    builtin_nodes: list[WorkflowNode]
    custom_nodes: list[WorkflowNode]
    
class NodeClassifier:
    """Service for classifying and categorizing workflow nodes."""

    def __init__(self):
        self.builtin_nodes = self._load_builtin_nodes()

    @staticmethod
    def _load_builtin_nodes() -> set[str]:
        """Load ComfyUI builtin nodes from data file."""
        global _BUILTIN_NODES
        if _BUILTIN_NODES is not None:
            return _BUILTIN_NODES

        builtin_nodes_path = Path(__file__).parent.parent / "data" / "comfyui_builtin_nodes.json"
        try:
            with open(builtin_nodes_path, encoding='utf-8') as f:
                data = json.load(f)
                _BUILTIN_NODES = set(data["all_builtin_nodes"])
                logger.debug(f"Loaded {len(_BUILTIN_NODES)} builtin nodes")
                return _BUILTIN_NODES
        except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to load builtin nodes: {e}")
            _BUILTIN_NODES = set()
            return _BUILTIN_NODES

    def get_custom_node_types(self, workflow: Workflow) -> set[str]:
        """Get custom node types from workflow."""
        return workflow.node_types - self.builtin_nodes

    def get_model_loader_nodes(self, workflow: Workflow, model_config: ModelConfig) -> list[WorkflowNode]:
        """Get model loader nodes from workflow."""
        return [node for node in workflow.nodes.values() if model_config.is_model_loader_node(node.type)]

    def classify_nodes(self, workflow: Workflow) -> NodeClassifierResult:
        """Classify all nodes by type."""
        builtin_nodes: list[WorkflowNode] = []
        custom_nodes: list[WorkflowNode] = []

        for node in workflow.nodes.values():
            if node.type in self.builtin_nodes:
                builtin_nodes.append(node)
            else:
                custom_nodes.append(node)

        return NodeClassifierResult(builtin_nodes, custom_nodes)
