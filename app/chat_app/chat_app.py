import polars as pl
from pathlib import Path # Imported pathlib
import json

from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import APIRouter, HTTPException, Depends, status, Request, Response, BackgroundTasks

from pydantic_models.pydantic_models import LLMProvider, ChatMessage, LLMChatLog
from loguru import logger
from configs.prometheus_metrics import monitor_function

from llm_logic.llm_prompts import EXTRACTION_PROMPT, INSIGHT_PROMPT

from llm_logic.llm_logic import query_llm
from llm_logic.llm_logs_db import DBManager

from drm_viz.data_review_viz import TAB_1_INDICATORS, color_palettes, data, target_data, get_actual, get_target

from llm_logic.llm_datashare_graphs import generate_chat_graph_json, build_performance_fig_json

from configs.util_configs import get_settings

settings = get_settings()


reload1=settings.ENV_PROD_DEV

if reload1=="PROD":
    CHAT_APP_URL=f"http://{settings.DOMAIN_PORTLESS_PROD}:{settings.DEFAULT_PORT}"

elif reload1=="DEV":        
    CHAT_APP_URL=f"http://{settings.DOMAIN_CHAT_PORTLESS_DEV}:{settings.DEFAULT_PORT}"


# Build an OS-independent absolute path 2 levels above this script's directory
# .resolve() gets the absolute path
# .parent (1st) = current directory | .parent (2nd) = one level up | .parent (3rd) = two levels up
base_dir = Path(__file__).resolve().parent.parent

# --- 1. CHAT LLM INTEGRATION & ENDPOINTS ---

# Setup Jinja Templates
templates = Jinja2Templates(directory=str(base_dir / "templates"))


chat_app_router = APIRouter(prefix="/chat_app", 
                   tags=["Chat Component"],
                   responses={404:{"Description":"Page Not Found"}})

# The base chat API entpoint.



@chat_app_router.get("/chat", response_class=HTMLResponse)
async def serve_chat_ui(request: Request):
    return templates.TemplateResponse("chat.html", 
                                      {"request": request, 
                                       "chat_app_url": CHAT_APP_URL  # <-- Add this line to pass the variable
                                       })






#@chat_app_router.post("/api/chat")
#async def handle_chat(req: ChatMessage):
#    # Step 1: Use LLM to extract intent (Parameter extraction)
#    extraction_prompt = f"""
#    Analyze the user's message and extract the target HIV/Health indicator and location.
#    Available Indicators: HTS_TST, HTS_TST_POS, TX_NEW, PrEP_NEW, TX_CURR.
#    User Message: "{req.message}"
#    Return ONLY a raw JSON object with keys "indicator" and "county". If not specified, use "All" for county and "HTS_TST" for indicator.
#    Example: {{"indicator": "TX_NEW", "county": "Nairobi"}}
#    """
#    
#    try:
#        # We use a fast, structured call here.
#        intent_json_str = await query_llm(extraction_prompt, req.provider, "You are a JSON parser. Output only JSON.")
#        intent_json_str = intent_json_str.replace("```json", "").replace("```", "").strip()
#        params = json.loads(intent_json_str)
#        indicator = params.get("indicator", "HTS_TST")
#        county = params.get("county", "All")
#    except Exception as e:
#        indicator, county = "HTS_TST", "All"
#
#    # Step 2: Generate Graph JSON using the extracted parameters
#    graph_json = generate_chat_graph_json(indicator, county)
#    
#    # Step 3: Use LLM to generate recommendations based on the user request and intent
#    insight_prompt = f"""
#    The user asked: "{req.message}".
#    I have queried the database for Indicator: {indicator}, County: {county}.
#    Provide a brief, professional summary of what they should look for in the chart, and 2 actionable programmatic recommendations for improving {indicator} performance. Keep it under 3 paragraphs. Do not mention the JSON.
#    """
#    text_response = await query_llm(insight_prompt, req.provider)
#    
#    # Step 4: Return both the LLM text and the Plotly Graph JSON
#    return {
#        "text": text_response,
#        "graph": graph_json
#    }


@chat_app_router.post("/v1api/chat")
async def handle_chat(request:Request, req: ChatMessage, background_tasks: BackgroundTasks):
    # Set the LLM tier state from request
    request.state.llm_tier = req.tier if (hasattr(req, "tier") and req.tier) else None

    # Step 1: Use LLM to extract intent (Parameter extraction)
    extraction_prompt = EXTRACTION_PROMPT.format(message=req.message)

    if req.provider != settings.DEFAULT_LLM:
        llm_provider=settings.DEFAULT_LLM
    else:
        llm_provider = req.provider
    
    logger.info("1: Default LLM set")

    intent_json_str = None
    try:
        # We use a fast, structured call here.
        logger.info("2: Right before query parameters extracted from user request.")
        with monitor_function("llm_queries", "parameter_extraction"):
            raw_intent = await query_llm(request=request,prompt=extraction_prompt, provider=llm_provider, system_prompt="You are a JSON parser. Output only JSON.")
        if hasattr(raw_intent, "content") and isinstance(raw_intent.content, str):
            intent_json_str = raw_intent.content
        elif hasattr(raw_intent, "text"):
            intent_json_str = raw_intent.text
        elif hasattr(raw_intent, "choices"):
            intent_json_str = raw_intent.choices[0].message.content
        else:
            intent_json_str = str(raw_intent)
        logger.info("3: After query parameters extracted from user request.")
        intent_json_str_clean = intent_json_str.replace("```json", "").replace("```", "").strip()
        params = json.loads(intent_json_str_clean)
        indicator = params.get("indicator", "HTS_TST")
        county = params.get("county", "All")
    except Exception as e:
        logger.warning(f"2: Failed to parse the user request, uses default. Error: {str(e)}")
        indicator, county = "HTS_TST", "All"

    # Step 2: Generate Graph JSON using the extracted parameters
    logger.info("4: Right before graphing the request.")
    with monitor_function("chat_api", "graph_generation"):
        graph_json = generate_chat_graph_json(indicator, county)
    logger.info("5: After graphing request and Right before the insight generations prompt is triggered.")
    # Step 3: Use LLM to generate recommendations based on the user request and intent
    insight_prompt = INSIGHT_PROMPT.format(message=req.message,indicator=indicator,county=county)
    with monitor_function("llm_queries", "insights_generation"):
        text_response = await query_llm(request=request,prompt=insight_prompt, provider=llm_provider)

    logger.info("6: Right after insights are generated.")
    
    # Extract string safely for logging
    extracted_insights_text = None
    if text_response:
        if hasattr(text_response, "content") and isinstance(text_response.content, str):
            extracted_insights_text = text_response.content
        elif hasattr(text_response, "text"):
            extracted_insights_text = text_response.text
        elif hasattr(text_response, "choices"):
            extracted_insights_text = text_response.choices[0].message.content
        else:
            extracted_insights_text = str(text_response)

    # Persist log to PostgreSQL in background
    log_entry = LLMChatLog(
        thread_id=req.thread_id,
        provider=llm_provider,
        user_prompt=req.message,
        extraction_prompt_response=intent_json_str,
        insights_prompt_response=extracted_insights_text
    )
    background_tasks.add_task(DBManager.log_interaction_model, log_entry)
    
    # Step 4: Return both the LLM text and the Plotly Graph JSON
    return {
        "text": text_response,
        "graph": graph_json
    }




@chat_app_router.post("/api/chat")
async def handle_chat(req: ChatMessage, request: Request, background_tasks: BackgroundTasks):
    # Set the LLM tier state from request
    request.state.llm_tier = req.tier if (hasattr(req, "tier") and req.tier) else None

    # ---------------------------------------------------------
    # STEP 1: PROMPT ENGINEERING - EXTRACT STRUCTURED QUERIES
    # ---------------------------------------------------------

    logger.info("1: Right before extraction prompt is created.")

    tab1_indicators=', '.join([i['id'] for i in TAB_1_INDICATORS])
    extraction_prompt = EXTRACTION_PROMPT.format(message=req.message,tab1_indicators=tab1_indicators)

    if req.provider != settings.DEFAULT_LLM:
        llm_provider=settings.DEFAULT_LLM
    else:
        llm_provider = req.provider
    
    logger.info("2: Default LLM set")

    intent_json_str = None
    try:
        logger.info("3: Before parameter extraction is done by LLM.")
        with monitor_function("llm_queries", "parameter_extraction"):
            raw_intent = await query_llm(request=request,prompt=extraction_prompt, provider=llm_provider, system_prompt="You are a JSON parser. Output only valid JSON.")
        # EXTRACT STRING SAFEGUARD: Ensure we have a string before replacing/parsing
        if hasattr(raw_intent, "content") and isinstance(raw_intent.content, str):
            intent_json_str = raw_intent.content
        elif hasattr(raw_intent, "text"):
            intent_json_str = raw_intent.text
        elif hasattr(raw_intent, "choices"): 
            intent_json_str = raw_intent.choices[0].message.content
        else:
            intent_json_str = str(raw_intent)
            
        intent_json_str = intent_json_str.replace("```json", "").replace("```", "").strip()
        parsed_intent = json.loads(intent_json_str)
        queries = parsed_intent.get("queries", [])
        logger.info("4: After parameter extraction is done by LLM")
        logger.info(f"5: The extracted queries are: {queries}")
        if queries == []:
            queries = [{"indicator": "HTS_TST", "filters": {}, "group_by": "County"}]
        else:
            queries

    except Exception as e:
        logger.error(f"❌ Extraction Failed. Error: {str(e)}")
        # Fallback to a default query if parsing fails
        queries = [{"indicator": "HTS_TST", "filters": {}, "group_by": "County"}]
        logger.warning(f"⚠️ Fallback activated: {queries}")

    # ---------------------------------------------------------
    # STEP 2: DYNAMIC DATA FETCHING & JSON CHART GENERATION
    # ---------------------------------------------------------
    colors = color_palettes["Default (Image Style)"]
    compiled_data_for_llm = {}
    chart_jsons = []

    logger.info("6: Application of extracted parameters to dataset.")

    with monitor_function("chat_api", "graph_generation"):
        for idx, q in enumerate(queries):
            ind_id = q.get("indicator", "HTS_TST")
            filters = q.get("filters", {})
            group_by = q.get("group_by", "County")
            
            # Apply filters lazily
            dff_chat = data
            dff_chat_tgt = target_data
            
            for col, val in filters.items():
                if val and val != "All":
                    dff_chat = dff_chat.filter(pl.col(col) == val)
                    dff_chat_tgt = dff_chat_tgt.filter(pl.col(col) == val)
                    
            # Collect into memory
            dff_chat = dff_chat.collect()
            dff_chat_tgt = dff_chat_tgt.collect()
            
            # Get unique grouping locations
            locs = dff_chat[group_by].unique().drop_nulls().to_list() if not dff_chat.is_empty() and group_by in dff_chat.columns else []
            
            chart_data = []
            max_period = dff_chat["Period"].drop_nulls().max() if not dff_chat.is_empty() and "Period" in dff_chat.columns else None

            for loc in locs:
                loc_df = dff_chat.filter(pl.col(group_by) == loc)
                loc_tgt_df = dff_chat_tgt.filter(pl.col(group_by) == loc)
                
                ach = get_actual(loc_df, ind_id, max_period)
                tgt = get_target(loc_tgt_df, ind_id)
                chart_data.append({group_by: loc, "Target": tgt, "Achieved": ach})
                
            _df = pl.DataFrame(chart_data)
            if not _df.is_empty():
                _df = _df.with_columns(
                    pl.when(pl.col("Target") == 0)
                    .then(pl.when(pl.col("Achieved") > 0).then(100.0).otherwise(0.0))
                    .otherwise((pl.col("Achieved") / pl.col("Target")) * 100).round(0).alias("% Achieved")
                )
                
                # Store data as a dictionary string for the LLM
                query_name = f"Query {idx+1}: {ind_id} grouped by {group_by} (Filters: {filters})"
                compiled_data_for_llm[query_name] = _df.to_dicts()
                
                # Generate the Plotly JSON
                fig_json = build_performance_fig_json(_df, group_by, ind_id, colors)
                if fig_json:
                    chart_jsons.append(fig_json)

    # ---------------------------------------------------------
    # STEP 3: GROUNDED TEXTUAL ANALYSIS
    # ---------------------------------------------------------
    tabular_data=json.dumps(compiled_data_for_llm, indent=2)

    logger.info("7: Before insight prompt is architected.")

    insight_prompt = INSIGHT_PROMPT.format(message=req.message,tabular_data=tabular_data)
    
    try:
        with monitor_function("llm_queries", "insights_generation"):
            raw_response = await query_llm(request=request,prompt=insight_prompt, provider=llm_provider)

        # FIX: The SSLSocket killer. 
        # Extract the pure string from whatever object `query_llm` returned.
        if hasattr(raw_response, "content") and isinstance(raw_response.content, str):
            text_response = raw_response.content
        elif hasattr(raw_response, "text"):
            text_response = raw_response.text
        elif hasattr(raw_response, "choices"): # Common structure for OpenAI SDK objects
            text_response = raw_response.choices[0].message.content
        else:
            # Fallback cast
            text_response = str(raw_response)

        logger.info("8: After insight prompt is run/ implemented.")
    
    except Exception as e:
        logger.error(f"❌ Extraction Failed. Error: {str(e)}")
        # Fallback to a default query if parsing fails
        fallback_indicator = queries[0]["indicator"]
        text_response = f"""The insights prompt failed, but below is the performance for {fallback_indicator}"""
        logger.warning(f"⚠️ Fallback activated: {queries}")

    # Persist log to PostgreSQL in background
    log_entry = LLMChatLog(
        thread_id=req.thread_id,
        provider=llm_provider,
        user_prompt=req.message,
        extraction_prompt_response=intent_json_str,
        insights_prompt_response=text_response
    )
    background_tasks.add_task(DBManager.log_interaction_model, log_entry)

    return {
        "text": text_response,
        "graphs": chart_jsons # Note: Returning a list of graphs now to handle comparisons
    }






"""
"""
