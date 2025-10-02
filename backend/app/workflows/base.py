"""Base workflow classes for LangGraph orchestration."""

from typing import Annotated, Any, NotRequired, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph


class WorkflowState(TypedDict):
    """Base state for all workflows."""

    input: str
    output: NotRequired[str]
    metadata: NotRequired[dict[str, Any]]
    error: NotRequired[str]


class BaseWorkflow:
    """Base class for LangGraph workflows."""

    def __init__(self):
        self.checkpointer = MemorySaver()
        self.graph = None

    def build(self) -> StateGraph:
        """
        Build the workflow graph.
        Should be overridden by subclasses.
        """
        raise NotImplementedError("Subclasses must implement build()")

    def compile(self):
        """Compile the workflow graph with checkpointing."""
        if not self.graph:
            self.graph = self.build()
        return self.graph.compile(checkpointer=self.checkpointer)

    async def run(self, initial_state: dict, config: dict | None = None) -> dict:
        """
        Execute the workflow.

        Args:
            initial_state: Initial state for the workflow
            config: Configuration including thread_id for checkpointing

        Returns:
            Final workflow state
        """
        compiled_graph = self.compile()
        result = await compiled_graph.ainvoke(initial_state, config=config or {})
        return result

    async def stream(self, initial_state: dict, config: dict | None = None):
        """
        Stream workflow execution.

        Args:
            initial_state: Initial state for the workflow
            config: Configuration including thread_id for checkpointing

        Yields:
            Workflow state updates
        """
        compiled_graph = self.compile()
        async for event in compiled_graph.astream(initial_state, config=config or {}):
            yield event
