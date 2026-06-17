from typing import Any, Callable, Optional, Type, TypeVar, get_origin, get_args, List, Set, Dict, Literal, Annotated, TypedDict

from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field, ConfigDict, IPvAnyAddress,model_validator,create_model

from langgraph.graph.message import add_messages

from prometheus_client import Histogram # NEW: For custom metrics

import decimal

from enum import Enum

import uuid



class LLMProvider(str, Enum):

    """
    The LLM used for agentic purposes, could be either of Options: 'openai', 'claude', 'gemini', 'vllm' 'sglang'.
    """

    OPENAI = "gpt-4o"
    CLAUDE_45 = "claude-opus-4-5"
    CLAUDE_46 = "claude-opus-4-6"
    GEMINI_3_PRO_PREVIEW = "gemini-3-pro-preview"
    GEMINI_3_FLASH_PREVIEW = "gemini-3-flash-preview"
    VLLM = "vllm"
    SGLANG = "sglang"




class GeminiLLMRequestType(str, Enum):

    """
    Type of API requested, pro or fast.
    """

    PRO = "pro"
    FAST = "fast"


class GeminiLLMCostType(str, Enum):


    """
    Type of Request: Paid or Free.
    """

    PAID = "paid"
    FREE = "free"


   


class ChatMessage(BaseModel):
    message: str = Field(...,description="The Human and AI messages that will be used as prompts to the LLM.")
    provider: LLMProvider = Field(...,description="The LLM used for agentic purposes, could be either of Options: 'openai', 'claude', 'gemini', 'vllm' 'sglang'.")
    thread_id: str = Field(...,description="The unique id for a particular chat for uniquely identifying them in the checkpointer.")
    tier: Optional[Literal["paid", "free"]] = Field(default=None, description="The LLM tier to use (paid or free).")
     



# --- 1. SCHEMAS & STATE ---

class QueryFilter(BaseModel):
    """Represents a specific slice of data for the query."""
    indicator: str = Field(default="HTS_TST", description="The HIV/Health indicator.")
    filters: Dict[str, str] = Field(
        default_factory=dict,
        description="Key-value pairs for filters. Keys must be strictly: County, Sub County, Ward, PRISM Facility Name, FY, Quarter, Period, Gender, Coarse Age Group, Finer Age Group."
    )
    group_by: str = Field(default="County", description="The column to group the data by on the x-axis or table rows.")




class GraphIntent(BaseModel):
    """The master intent parsed from the user."""
    graph_type: Literal["performance_vs_target", "linkage_cascade", "testing_efficiency", "prep_cascade", "unknown", "comparison"] = Field(
        ..., description="The analytical view. Use 'comparison' if evaluating two or more distinct locations/periods."
    )
    render_mode: Literal["graph", "table", "text_only"] = Field(
        ..., description="Choose 'graph' for trends/comparisons of < 15 items. Choose 'table' for large datasets, exact number lookups, or > 15 items. Choose 'text_only' if no data visualization is needed."
    )
    queries: List[QueryFilter] = Field(..., description="A list of distinct queries. Will contain multiple items if comparing Nyamira vs Vihiga.")




class AgentState(TypedDict):
    """The shared state for the LangGraph workflow."""
    messages: Annotated[list, add_messages]
    provider: str # The requested LLM provider (openai, gemini, sglang)
    intent: Optional[Any]
    validation_status: Literal["valid", "invalid", "pending"]
    clarification_message: Optional[str]
    raw_data_dicts: List[Dict[str, Any]]
    plotly_jsons: List[str]
    tables_html: List[str]
    final_response: str


class LLMChatLog(BaseModel):
    query_id: uuid.UUID = Field(default_factory=uuid.uuid4, description="Unique identifier for each query.")
    thread_id: str = Field(..., description="Unique thread identifier for the chat session.")
    provider: str = Field(..., description="LLM provider name.")
    user_prompt: str = Field(..., description="The original user message prompt.")
    extraction_prompt_response: Optional[str] = Field(default=None, description="The response from the intent EXTRACTION_PROMPT.")
    insights_prompt_response: Optional[str] = Field(default=None, description="The response from the analytical INSIGHT_PROMPT.")
    timestamp: Optional[datetime] = Field(default=None, description="Timestamp of logging.")


# --- CUSTOM PROMETHEUS METRICS ---
POLARS_PROCESSING_TIME = Histogram(
    "polars_processing_seconds",
    "Time spent aggregating data in Polars",
    ["graph_type"]
)



LLM_LATENCY = Histogram(
    "llm_latency_seconds",
    "Time spent waiting for OpenAI/LLM response",
    ["node_name"]
)


