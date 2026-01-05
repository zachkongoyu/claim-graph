"""Tests for router logic and workflow."""
import pytest
from app.graph.supervisor import supervisor_router
from app.models.graph_state import GraphState


def test_supervisor_router_initial_state():
    """Test supervisor router with initial state."""
    state: GraphState = {
        "resource_ids": ["test-1"],
        "extracted_data": None,
        "coded_data": None,
        "audit_result": None,
        "retry_count": 0,
        "max_retries": 3,
        "next_action": None,
        "error": None,
    }
    
    result = supervisor_router(state)
    assert result == "extractor"


def test_supervisor_router_code_action():
    """Test supervisor router routing to coder."""
    state: GraphState = {
        "resource_ids": ["test-1"],
        "extracted_data": None,
        "coded_data": None,
        "audit_result": None,
        "retry_count": 0,
        "max_retries": 3,
        "next_action": "code",
        "error": None,
    }
    
    result = supervisor_router(state)
    assert result == "coder"


def test_supervisor_router_audit_action():
    """Test supervisor router routing to auditor."""
    state: GraphState = {
        "resource_ids": ["test-1"],
        "extracted_data": None,
        "coded_data": None,
        "audit_result": None,
        "retry_count": 0,
        "max_retries": 3,
        "next_action": "audit",
        "error": None,
    }
    
    result = supervisor_router(state)
    assert result == "auditor"


def test_supervisor_router_retry_action():
    """Test supervisor router retry logic."""
    state: GraphState = {
        "resource_ids": ["test-1"],
        "extracted_data": None,
        "coded_data": None,
        "audit_result": None,
        "retry_count": 1,
        "max_retries": 3,
        "next_action": "retry_code",
        "error": None,
    }
    
    result = supervisor_router(state)
    assert result == "coder"


def test_supervisor_router_end_action():
    """Test supervisor router end condition."""
    state: GraphState = {
        "resource_ids": ["test-1"],
        "extracted_data": None,
        "coded_data": None,
        "audit_result": None,
        "retry_count": 0,
        "max_retries": 3,
        "next_action": "end",
        "error": None,
    }
    
    result = supervisor_router(state)
    assert result == "end"


def test_supervisor_router_error_condition():
    """Test supervisor router with error state."""
    state: GraphState = {
        "resource_ids": ["test-1"],
        "extracted_data": None,
        "coded_data": None,
        "audit_result": None,
        "retry_count": 0,
        "max_retries": 3,
        "next_action": None,
        "error": "Test error",
    }
    
    result = supervisor_router(state)
    assert result == "end"
