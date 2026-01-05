"""LangGraph workflow definition."""
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from app.models.graph_state import GraphState
from app.graph.nodes import extractor_node, coder_node, auditor_node
from app.graph.supervisor import supervisor_router
import logging

logger = logging.getLogger(__name__)


def create_workflow() -> StateGraph:
    """
    Create the LangGraph workflow for RCM processing.
    
    Workflow:
    1. Supervisor routes to Extractor
    2. Extractor extracts medical info -> routes to Coder
    3. Coder assigns medical codes -> routes to Auditor
    4. Auditor validates:
       - If pass: end
       - If fail and retries left: route back to Coder
       - If fail and no retries: end
    """
    # Create the graph
    workflow = StateGraph(GraphState)
    
    # Add nodes
    workflow.add_node("extractor", extractor_node)
    workflow.add_node("coder", coder_node)
    workflow.add_node("auditor", auditor_node)
    
    # Add conditional routing from supervisor
    workflow.add_conditional_edges(
        "extractor",
        lambda state: supervisor_router(state),
        {
            "coder": "coder",
            "end": END,
        }
    )
    
    workflow.add_conditional_edges(
        "coder",
        lambda state: supervisor_router(state),
        {
            "auditor": "auditor",
            "end": END,
        }
    )
    
    workflow.add_conditional_edges(
        "auditor",
        lambda state: supervisor_router(state),
        {
            "coder": "coder",  # Retry path
            "end": END,
        }
    )
    
    # Set entry point
    workflow.set_entry_point("extractor")
    
    return workflow


def run_workflow(resource_ids: list[str], max_retries: int = 3) -> Dict[str, Any]:
    """
    Execute the workflow on given resource IDs.
    
    Args:
        resource_ids: List of FHIR resource IDs to process
        max_retries: Maximum number of retry attempts for failed audits
    
    Returns:
        Final state after workflow completion
    """
    logger.info(f"Running workflow on {len(resource_ids)} resources")
    
    # Create initial state
    initial_state: GraphState = {
        "resource_ids": resource_ids,
        "extracted_data": None,
        "coded_data": None,
        "audit_result": None,
        "retry_count": 0,
        "max_retries": max_retries,
        "next_action": None,
        "error": None,
    }
    
    # Create and compile workflow
    workflow = create_workflow()
    app = workflow.compile()
    
    # Run workflow
    final_state = app.invoke(initial_state)
    
    logger.info("Workflow completed")
    return final_state
