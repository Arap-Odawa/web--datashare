



EXTRACTION_PROMPT_V1 = """
    Analyze the user's message and extract the target HIV/Health indicator and location.
    Available Indicators: HTS_TST, HTS_TST_POS, TX_NEW, PrEP_NEW, TX_CURR.
    User Message: "{message}"
    Return ONLY a raw JSON object with keys "indicator" and "county". If not specified, use "All" for county and "HTS_TST" for indicator.
    Example: {{"indicator": "TX_NEW", "county": "Nyamira"}}
    """


EXTRACTION_PROMPT_V2 = """
    You are an analytical router for a health data dashboard.
    Analyze the user's message and break it down into a list of specific data queries.
    If the user asks for a comparison, create separate query objects for each side of the comparison.
    
    Available Indicators: {tab1_indicators}
    Available Geographic Groupings (group_by): County, Sub County, Ward, PRISM Facility Name.
    Available Filters: FY, Quarter, Period, County, Sub County, Ward.

    User Message: "{message}"
    
    Return strictly a JSON object with a "queries" array. Example format:
    {{
      "queries": [
        {{
          "indicator": "HTS_TST",
          "filters": {{"County": "Nyamira"}},
          "group_by": "Ward"
        }},
        {{
          "indicator": "HTS_TST",
          "filters": {{"County": "Vihiga"}},
          "group_by": "Sub County"
        }}
      ]
    }}
    """


"""

####################################################################################################################################################################################
####################################################################################################################################################################################
####################################################################################################################################################################################



Date: 22/03/2026.
Notes on Below Extraction Prompt:

PROMPT:
review the below EXTRACTION_PROMPT to see if we can tighten its instructions so the LLM reliably outputs parseable 
JSON.

EXTRACTION_PROMPT = "
    You are an analytical router for a health data dashboard.
    Analyze the user's message and break it down into a list of specific data queries.
    If the user asks for a comparison, create separate query objects for each side of the comparison.
    
    Available Indicators: {tab1_indicators}
    Available Geographic Groupings (group_by): County, Sub County, Ward, PRISM Facility Name.
    Available Filters: FY, Quarter, Period, County, Sub County, Ward.

    User Message: "{message}"
    
    Return strictly a JSON object with a "queries" array. Example format:
    {{
      "queries": [
        {{
          "indicator": "HTS_TST",
          "filters": {{"County": "Nyamira"}},
          "group_by": "Ward"
        }},
        {{
          "indicator": "HTS_TST",
          "filters": {{"County": "Vihiga"}},
          "group_by": "Sub County"
        }}
      ]
    }}
    "


RESPOSNE FROM GEMINI:

To ensure an LLM reliably outputs parseable JSON, you have to treat it less like a conversational assistant and 
more like a strict API endpoint. 

The primary issue with the original prompt is that it leaves room for the LLM to be "helpful" by adding 
conversational filler (e.g., *"Here is the JSON you requested:"*) or wrapping the output in Markdown blocks 
(e.g., ````json ... ````), which immediately breaks `json.loads()`.

Here is a significantly tightened version of your `EXTRACTION_PROMPT`. 

### The Revised Extraction Prompt

```python
EXTRACTION_PROMPT = "
You are a backend API data routing processor for a health data dashboard. Your SOLE purpose is to extract 
parameters from the user's message and output them as a raw JSON object.

CRITICAL INSTRUCTIONS:
1. OUTPUT ONLY VALID JSON.
2. DO NOT include greetings, explanations, or conversational text.
3. DO NOT wrap the output in Markdown formatting or backticks (e.g., do not use ```json).
4. The output must start with {{ and end with }}.

# AVAILABLE PARAMETERS:
- Indicators: {tab1_indicators}
- Geographic Groupings (group_by): County, Sub County, Ward, PRISM Facility Name.
- Filters: FY, Quarter, Period, County, Sub County, Ward.

# EXTRACTION RULES:
1. Comparisons: If the user compares entities (e.g., Nyamira vs. Vihiga), create separate query objects in the array for each side.
2. Filtering: Map identified locations or timeframes to the "filters" object.
3. Grouping: Determine the most logical "group_by" based on the request (e.g., "performance of wards in Nyamira" -> group_by: "Ward", filters: {{"County": "Nyamira"}}).
4. Fallback: If the user's message is ambiguous, unrelated, or lacks a specific indicator, default to: {{"queries": [{{"indicator": "HTS_TST", "filters": {{}}, "group_by": "County"}}]}}

# REQUIRED JSON SCHEMA:
{{
  "queries": [
    {{
      "indicator": "<String: Exact match from Available Indicators>",
      "filters": {{"<String: Filter Name>": "<String: Filter Value>"}},
      "group_by": "<String: Exact match from Available Geographic Groupings>"
    }}
  ]
}}

User Message: "{message}"
"
```

### Why these changes make it bulletproof:

* **Persona Shift:** By telling the model it is a "backend API data routing processor" instead of an "analytical 
    router," it adopts a much more mechanical, less conversational posture.
* **The "Negative" Constraints:** Explicitly banning Markdown backticks and conversational text 
    (`DO NOT include...`) is often more effective than just asking it to "strictly return JSON."
* **The "Structural" Constraints:** Telling it that the first character must be `{` and the last must be `}` 
    prevents introductory or concluding remarks.
* **Built-in Fallback:** Instructing the LLM directly on what to do when it gets confused (Rule 4) prevents it from 
    writing an error message in plain text when it doesn't understand the user's query.

Would you like me to take a look at your `INSIGHT_PROMPT` next to see if we can optimize how the model interprets 
the raw Polars data we are injecting into it?



####################################################################################################################################################################################
####################################################################################################################################################################################
####################################################################################################################################################################################

"""




EXTRACTION_PROMPT = """
You are a backend API data routing processor for a health data dashboard. Your SOLE purpose is to extract parameters from the user's message and output them as a raw JSON object.

CRITICAL INSTRUCTIONS:
1. OUTPUT ONLY VALID JSON.
2. DO NOT include greetings, explanations, or conversational text.
3. DO NOT wrap the output in Markdown formatting or backticks (e.g., do not use ```json).
4. The output must start with {{ and end with }}.

# AVAILABLE PARAMETERS:
- Available Indicators: {tab1_indicators}
- Available Geographic Groupings (group_by): County, Sub County, Ward, PRISM Facility Name.
- Filters: FY, Quarter, Period, County, Sub County, Ward.

# EXTRACTION RULES:
1. Comparisons: If the user compares entities (e.g., Nyamira vs. Vihiga), create separate query objects in the array for each side.
2. Filtering: Map identified locations or timeframes to the "filters" object.
3. Grouping: Determine the most logical "group_by" based on the request (e.g., "performance of wards in Nyamira" -> group_by: "Ward", filters: {{"County": "Nyamira"}}).
4. Fallback: If the user's message is ambiguous, unrelated, or lacks a specific indicator, default to: {{"queries": [{{"indicator": "HTS_TST", "filters": {{}}, "group_by": "County"}}]}}

# REQUIRED JSON SCHEMA:
{{
  "queries": [
    {{
      "indicator": "<String: Exact match from Available Indicators>",
      "filters": {{"<String: Filter Name>": "<String: Filter Value>"}},
      "group_by": "<String: Exact match from Available Geographic Groupings>"
    }}
  ]
}}

Return strictly a JSON object with a "queries" array. Example format:
    {{
      "queries": [
        {{
          "indicator": "HTS_TST",
          "filters": {{"County": "Nyamira"}},
          "group_by": "Ward"
        }},
        {{
          "indicator": "HTS_TST",
          "filters": {{"County": "Vihiga"}},
          "group_by": "Sub County"
        }}
      ]
    }}


User Message: "{message}"
"""




INSIGHT_PROMPT_V1 = """
    The user asked: "{message}".
    I have queried the database for Indicator: {indicator}, County: {county}.
    Provide a brief, professional summary of what they should look for in the chart, and 2 actionable programmatic recommendations for improving {indicator} performance. Keep it under 3 paragraphs. Do not mention the JSON.
    """

INSIGHT_PROMPT_V2 ="""
    The user asked: "{message}".
    
    I have queried the database based on their request. Here is the exact, aggregated numerical data returned from the backend:
    
    {tabular_data}
    
    Using ONLY the numbers provided in the JSON data above, provide a comparative analysis or direct answer to the user's question. 
    Point out the highest and lowest performers based on '% Achieved' or total 'Achieved'.
    Provide 2 actionable insights. Keep the tone professional and concise. 
    Do not mention the JSON structure directly to the user, just synthesize the numbers naturally.
    """

"""

####################################################################################################################################################################################
####################################################################################################################################################################################
####################################################################################################################################################################################

Date: 22/03/2026.
Notes on Below Insight Prompt:

PROMPT:

look at the below  INSIGHT_PROMPT next to see if we can optimize how the model interprets the raw Polars data we 
are injecting into it


INSIGHT_PROMPT ="
    The user asked: "{message}".
    
    I have queried the database based on their request. Here is the exact, aggregated numerical data returned from the backend:
    
    {tabular_data}
    
    Using ONLY the numbers provided in the JSON data above, provide a comparative analysis or direct answer to the user's question. 
    Point out the highest and lowest performers based on '% Achieved' or total 'Achieved'.
    Provide 2 actionable insights. Keep the tone professional and concise. 
    Do not mention the JSON structure directly to the user, just synthesize the numbers naturally.
    "


GEMINI RESPONSE:

Your current `INSIGHT_PROMPT` is actually quite good—it includes the crucial "Use ONLY the numbers provided" 
guardrail, which is the gold standard for preventing LLM hallucinations in data apps. 

However, we can optimize it to solve three common edge cases that usually crop up when building these systems:
1.  **The "Wall of Text" Problem:** LLMs tend to write dense paragraphs. We need to force it to use scannable 
    formatting (bullet points, bold text).
2.  **The "Empty Data" Crash:** If a user queries a Ward that didn't report data for a specific quarter, the 
    `{tabular_data}` will be empty (`{}` or `[]`). The LLM needs instructions on how to handle this gracefully 
    instead of hallucinating a response or apologizing profusely.
3.  **Generic Insights:** "Actionable insights" can sometimes devolve into *"You should improve the lowest 
    performer."* We can steer the LLM toward health-domain-specific programmatic actions.

Here is the optimized `INSIGHT_PROMPT`.

### The Optimized Insight Prompt

```python
INSIGHT_PROMPT = "
You are a Senior Global Health Data Analyst presenting findings in a Data Review Meeting.
The user asked: "{message}"

Here is the exact, aggregated numerical data returned from the database for this query:
{tabular_data}

# INSTRUCTIONS:
1. STRICT GROUNDING: You must base your analysis EXCLUSIVELY on the numbers provided above. Do not hallucinate external statistics or assume unprovided baseline data.
2. EMPTY DATA CHECK: If the provided data is empty (e.g., {{}} or []), simply state that no data was reported for those specific parameters and suggest they adjust their filters (e.g., check the Quarter or County). Stop processing further.
3. DIRECT ANSWER: Provide a 1-2 sentence direct answer summarizing the core trend related to the user's question.
4. PERFORMANCE EXTREMES: Explicitly identify the highest and lowest performers. Prioritize using '% Achieved' if available; otherwise, use total 'Achieved'. 
5. PROGRAMMATIC ACTION: Provide exactly 2 concise, actionable programmatic recommendations based on the variance in the numbers (e.g., targeted site mentorship, commodity redistribution, or deep-dive investigations into reporting gaps).

# FORMATTING RULES:
- Keep the tone professional, objective, and highly concise.
- Use clear bullet points (-) for the performance extremes and insights to ensure readability.
- **Bold** the names of the geographic locations (Counties, Wards) and the specific metric names for quick scannability.
- CRITICAL: NEVER mention "JSON", "the data provided", "the dictionary", or "the backend". Speak naturally as if you ran the analysis yourself.
"
```

### Why these optimizations matter:
* **Persona Assignment ("Senior Global Health Data Analyst"):** This primes the model's vocabulary. It will naturally start using terminology appropriate for PEPFAR/MOH reporting rather than generic business speak.
* **Empty Data Check:** By explicitly catching the `{}`, you prevent the LLM from trying to invent a narrative out of thin air if your Polars filtering results in an empty dataframe.
* **Formatting Rules:** By demanding bullet points and bolding, the text response rendered in your `chat.html` will be much easier for a user to read quickly, especially on mobile devices.

### A Quick Note on the Frontend Rendering
Because this optimized prompt specifically asks the LLM to use Markdown (like `**bolding**`), you might notice that your current JavaScript (`innerHTML = text.replace(/\n/g, "<br>");`) will literally print out `**Nyamira**` instead of rendering it as bold text. 

To fix this so the formatting looks beautiful, you can add a tiny, lightweight Markdown parser to your `chat.html`. 

Just add this script tag to your `<head>`:
```html
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
```

And update the text rendering line in your `renderAIResponse` JavaScript function from this:
```javascript
textDiv.innerHTML = text.replace(/\n/g, "<br>");
```
To this:
```javascript
textDiv.innerHTML = marked.parse(text);
```

Would you like to look at optimizing the Polars aggregations next to ensure the data payloads sent to the LLM 
remain small and lightning-fast?


####################################################################################################################################################################################
####################################################################################################################################################################################
####################################################################################################################################################################################



"""



INSIGHT_PROMPT = """
You are a Senior Global Health Data Analyst presenting findings in a Data Review Meeting.
The user asked: "{message}"

Here is the exact, aggregated numerical data returned from the database for this query:
{tabular_data}

# INSTRUCTIONS:
1. STRICT GROUNDING: You must base your analysis EXCLUSIVELY on the numbers provided above. Do not hallucinate external statistics or assume unprovided baseline data.
2. EMPTY DATA CHECK: If the provided data is empty (e.g., {{}} or []), simply state that no data was reported for those specific parameters and suggest they adjust their filters (e.g., check the Quarter or County). Stop processing further.
3. DIRECT ANSWER: Provide a 1-2 sentence direct answer summarizing the core trend related to the user's question.
4. PERFORMANCE EXTREMES: Explicitly identify the highest and lowest performers. Prioritize using '% Achieved' if available; otherwise, use total 'Achieved'. 
5. PROGRAMMATIC ACTION: Provide exactly 2 concise, actionable programmatic recommendations based on the variance in the numbers (e.g., targeted site mentorship, commodity redistribution, or deep-dive investigations into reporting gaps).

# FORMATTING RULES:
- Keep the tone professional, objective, and highly concise.
- Use clear bullet points (-) for the performance extremes and insights to ensure readability.
- **Bold** the names of the geographic locations (Counties, Wards) and the specific metric names for quick scannability.
- CRITICAL: NEVER mention "JSON", "the data provided", "the dictionary", or "the backend". Speak naturally as if you ran the analysis yourself.
"""







