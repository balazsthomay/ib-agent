"""Tests for LangGraph workflows."""

from unittest.mock import AsyncMock, patch

import pytest

from app.workflows.company_lookup import CompanyLookupWorkflow


@pytest.mark.asyncio
async def test_company_lookup_generate_query():
    """Test search query generation."""
    workflow = CompanyLookupWorkflow()
    state = {"company_name": "Tesla Inc"}

    with patch("app.workflows.company_lookup.llm_client.chat_completion") as mock_llm:
        mock_llm.return_value = "Tesla Inc financial metrics revenue"

        result = await workflow.generate_search_query(state)

        assert "search_query" in result
        assert result["search_query"] == "Tesla Inc financial metrics revenue"
        mock_llm.assert_called_once()


@pytest.mark.asyncio
async def test_company_lookup_generate_query_error():
    """Test error handling in query generation."""
    workflow = CompanyLookupWorkflow()
    state = {"company_name": "Tesla Inc"}

    with patch(
        "app.workflows.company_lookup.llm_client.chat_completion",
        side_effect=Exception("LLM error"),
    ):
        result = await workflow.generate_search_query(state)

        assert "error" in result
        assert "Failed to generate search query" in result["error"]


@pytest.mark.asyncio
async def test_company_lookup_search_skips_on_error():
    """Test that search is skipped if there's an error in state."""
    workflow = CompanyLookupWorkflow()
    state = {"company_name": "Tesla Inc", "error": "Previous error"}

    result = await workflow.search_company_info(state)

    assert result == {}


@pytest.mark.asyncio
async def test_company_lookup_extract_skips_on_error():
    """Test that extraction is skipped if there's an error in state."""
    workflow = CompanyLookupWorkflow()
    state = {"company_name": "Tesla Inc", "error": "Previous error"}

    result = await workflow.extract_structured_data(state)

    assert result == {}


@pytest.mark.asyncio
async def test_company_lookup_extract_structured_data():
    """Test structured data extraction."""
    workflow = CompanyLookupWorkflow()
    state = {
        "company_name": "Tesla Inc",
        "raw_data": "Tesla is an electric vehicle manufacturer...",
    }

    mock_json_response = {
        "name": "Tesla Inc",
        "website": "https://tesla.com",
        "industry": "Automotive",
        "description": "Electric vehicle manufacturer",
        "headquarters": "Austin, TX",
        "revenue": "$81.5B",
        "employees": "127855",
    }

    with patch("app.workflows.company_lookup.llm_client.chat_completion") as mock_llm:
        import json

        mock_llm.return_value = json.dumps(mock_json_response)

        result = await workflow.extract_structured_data(state)

        assert "structured_info" in result
        assert result["structured_info"]["name"] == "Tesla Inc"
        assert result["structured_info"]["website"] == "https://tesla.com"


@pytest.mark.asyncio
async def test_workflow_build():
    """Test workflow graph construction."""
    workflow = CompanyLookupWorkflow()
    graph = workflow.build()

    assert graph is not None
    # Verify nodes exist
    assert "generate_query" in graph.nodes
    assert "search" in graph.nodes
    assert "extract" in graph.nodes
