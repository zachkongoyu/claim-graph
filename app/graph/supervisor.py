"""Supervisor node that routes workflow."""
from typing import Dict, Any, Literal
from app.models.graph_state import GraphState
import logging

logger = logging.getLogger(__name__)


def supervisor_router(state: GraphState) -> Literal["extractor", "coder", "auditor", "end"]:
    """
    Supervisor node that determines next step in workflow.
    
    Routes based on:
    - Current next_action in state
    - Retry logic when audit fails
    - Error conditions
    """
    next_action = state.get("next_action")
    error = state.get("error")
    
    if error:
        logger.error(f"Error detected: {error}, ending workflow")
        return "end"
    
    if not next_action:
        # Start of workflow
        logger.info("Starting workflow with extractor")
        return "extractor"
    
    if next_action == "code":
        logger.info("Routing to coder")
        return "coder"
    
    if next_action == "audit":
        logger.info("Routing to auditor")
        return "auditor"
    
    if next_action == "retry_code":
        logger.info("Audit failed, retrying coder")
        return "coder"
    
    if next_action == "end":
        logger.info("Workflow complete")
        return "end"
    
    # Default fallback
    logger.warning(f"Unknown next_action: {next_action}, ending workflow")
    return "end"
