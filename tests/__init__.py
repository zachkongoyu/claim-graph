"""Tests package - configure test environment."""
import os

# Set test database URL before any app imports
# Use file-based database since in-memory databases are not shared across connections
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./data/test_claim_graph.db"
