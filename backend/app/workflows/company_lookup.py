"""Company information lookup workflow using LangGraph."""

from typing import NotRequired, TypedDict

from langgraph.graph import END, START, StateGraph

from app.services.browser import browser_manager
from app.services.llm_client import llm_client
from app.workflows.base import BaseWorkflow


class CompanyLookupState(TypedDict):
    """State for company lookup workflow."""

    company_name: str
    search_query: NotRequired[str]
    raw_data: NotRequired[str]
    structured_info: NotRequired[dict]
    error: NotRequired[str]


class CompanyLookupWorkflow(BaseWorkflow):
    """
    Workflow for looking up company information.

    Steps:
    1. Generate search query from company name
    2. Search web for company information
    3. Extract and structure relevant data
    """

    async def generate_search_query(self, state: CompanyLookupState) -> dict:
        """Generate an optimized search query for the company."""
        company_name = state["company_name"]

        prompt = f"""Generate a concise Google search query to find key financial and business information about: {company_name}

The query should help find:
- Official website
- Revenue and financial metrics
- Industry and sector
- Key executives
- Recent news

Return only the search query, nothing else."""

        try:
            query = await llm_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
            )

            return {"search_query": query.strip()}

        except Exception as e:
            return {"error": f"Failed to generate search query: {str(e)}"}

    async def search_company_info(self, state: CompanyLookupState) -> dict:
        """Search for company information using web scraping."""
        if "error" in state:
            return {}

        search_query = state.get("search_query", state["company_name"])

        # Use DuckDuckGo or other search engine
        search_url = f"https://lite.duckduckgo.com/lite/?q={search_query.replace(' ', '+')}"

        try:
            result = await browser_manager.scrape_page(
                url=search_url,
                wait_for_selector="body",
                timeout=10000,
            )

            return {"raw_data": result["text"]}

        except Exception as e:
            return {"error": f"Failed to search for company info: {str(e)}"}

    async def extract_structured_data(self, state: CompanyLookupState) -> dict:
        """Extract structured information from raw search results."""
        if "error" in state:
            return {}

        raw_data = state.get("raw_data", "")
        company_name = state["company_name"]

        prompt = f"""Extract key information about {company_name} from the following search results.

Return a JSON object with these fields (use null for unknown values):
- name: Official company name
- website: Official website URL
- industry: Industry/sector
- description: Brief company description
- headquarters: Location of headquarters
- revenue: Latest revenue figure (if available)
- employees: Number of employees (if available)

Search results:
{raw_data[:2000]}

Return only valid JSON, no other text."""

        try:
            response = await llm_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
            )

            # Parse JSON response
            import json

            structured_info = json.loads(response)

            return {"structured_info": structured_info}

        except Exception as e:
            return {"error": f"Failed to extract structured data: {str(e)}"}

    def build(self) -> StateGraph:
        """Build the company lookup workflow graph."""
        builder = StateGraph(CompanyLookupState)

        # Add nodes
        builder.add_node("generate_query", self.generate_search_query)
        builder.add_node("search", self.search_company_info)
        builder.add_node("extract", self.extract_structured_data)

        # Add edges
        builder.add_edge(START, "generate_query")
        builder.add_edge("generate_query", "search")
        builder.add_edge("search", "extract")
        builder.add_edge("extract", END)

        return builder


# Global workflow instance
company_lookup_workflow = CompanyLookupWorkflow()
