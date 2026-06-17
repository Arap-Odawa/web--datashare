
from  google import genai
import anthropic, openai
from fastapi import Request
#from openai import AsyncOpenAI
import requests

from langchain_openai import ChatOpenAI
from google import genai
#from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

from redis_cache_configs.redis_lifespan_configs import gemini_api_key_rotate_final_selection

from pydantic_models.pydantic_models import LLMProvider, ChatMessage

from pydantic_models.pydantic_models import (
    GeminiLLMRequestType,
    GeminiLLMCostType,

)

from configs.util_configs import get_settings

settings = get_settings()



# Boilerplate LLM Router
async def query_llm(request:Request, prompt: str, provider: str, system_prompt: str = "You are a helpful data assistant.") -> str:
    """Routes the prompt to the selected LLM provider."""
    
    #if provider == "openai":
    if provider == LLMProvider.OPENAI:
        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL_GPT40,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content

    #elif provider == "claude":
    elif provider == LLMProvider.CLAUDE_45:
        client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        #client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        response = await client.messages.create(
            model=settings.CLAUDE_MODEL_OPUS_46,
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

    #elif provider == "claude":
    elif provider == LLMProvider.CLAUDE_46:
        client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        #client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        response = await client.messages.create(
            model=settings.CLAUDE_MODEL_OPUS_46,
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

    #elif provider == "gemini":
    elif provider == LLMProvider.GEMINI_3_PRO_PREVIEW:
        #client = genai.Client(api_key=settings.GEMINI_API_KEY)
        client = await gemini_api_key_rotate_final_selection(request=request,fast_or_pro=GeminiLLMCostType.FREE, paid_or_free=GeminiLLMRequestType.PRO)

        # You must pass both the system prompt and the actual prompt instructions
        contents = f"System: {system_prompt}\n\nUser: {prompt}"

        try:
            #response = client.models.generate_content(model=settings.GEMINI_MODEL_3_PRO_PREVIEW,contents=contents,) # Synchronous
            response = await client.aio.models.generate_content(model=settings.GEMINI_MODEL_3_PRO_PREVIEW,contents=contents,) # Asynchronous
            return response.text
        
        except Exception as  e:
            raise e

    #elif provider == "gemini":
    elif provider == LLMProvider.GEMINI_3_FLASH_PREVIEW:
        #client = genai.Client(api_key=settings.GEMINI_API_KEY)
        client = await gemini_api_key_rotate_final_selection(request=request,fast_or_pro=GeminiLLMCostType.FREE, paid_or_free=GeminiLLMRequestType.FAST)
        #response = client.models.generate_content(model=settings.GEMINI_MODEL_3_FLASH_PREVIEW,contents=system_prompt,)
        #return response.text

        # You must pass both the system prompt and the actual prompt instructions
        contents = f"System: {system_prompt}\n\nUser: {prompt}"

        try:
            #response = client.models.generate_content(model=settings.GEMINI_MODEL_3_FLASH_PREVIEW,contents=contents,) # Synchronous
            response = await client.aio.models.generate_content(model=settings.GEMINI_MODEL_3_FLASH_PREVIEW,contents=contents,) # Asynchronous
            return response.text
        
        except Exception as  e:
            raise e

    elif provider == "vllm": # For locally hosted Qwen/DeepSeek via vLLM
        vllm_url = settings.VLLM_ENDPOINT
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": settings.QWEN_35_2B_INSTRUCT, # Change to your loaded model
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        }
        res = requests.post(vllm_url, headers=headers, json=payload)
        return res.json()["choices"][0]["message"]["content"]
    

    elif provider == "sglang": # For locally hosted Qwen/DeepSeek via SGLang
        vllm_url = settings.SGLANG_ENDPOINT
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": settings.QWEN_35_2B_INSTRUCT, # Change to your loaded model
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        }
        res = requests.post(vllm_url, headers=headers, json=payload)
        return res.json()["choices"][0]["message"]["content"] 
    return "Error: Invalid Provider."




# Boilerplate LLM Router
async def query_llm_old_non_rotating_gemini_keys(prompt: str, provider: str, system_prompt: str = "You are a helpful data assistant.") -> str:
    """Routes the prompt to the selected LLM provider."""
    
    #if provider == "openai":
    if provider == LLMProvider.OPENAI:
        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL_GPT40,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content

    #elif provider == "claude":
    elif provider == LLMProvider.CLAUDE_45:
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        #client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        response = await client.messages.create(
            model=settings.CLAUDE_MODEL_OPUS_46,
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

    #elif provider == "claude":
    elif provider == LLMProvider.CLAUDE_46:
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        #client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        response = await client.messages.create(
            model=settings.CLAUDE_MODEL_OPUS_46,
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

    #elif provider == "gemini":
    elif provider == LLMProvider.GEMINI_3_PRO_PREVIEW:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        try:
            response = client.models.generate_content(model=settings.GEMINI_MODEL_3_FLASH_PREVIEW,contents=system_prompt,)
            return response.text
        
        except Exception as  e:
            return e

    #elif provider == "gemini":
    elif provider == LLMProvider.GEMINI_3_FLASH_PREVIEW:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        response = client.models.generate_content(model=settings.GEMINI_MODEL_3_FLASH_PREVIEW,contents=system_prompt,)
        return response.text

    elif provider == "vllm": # For locally hosted Qwen/DeepSeek via vLLM
        vllm_url = settings.VLLM_ENDPOINT
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": settings.QWEN_35_2B_INSTRUCT, # Change to your loaded model
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        }
        res = requests.post(vllm_url, headers=headers, json=payload)
        return res.json()["choices"][0]["message"]["content"]
    

    elif provider == "sglang": # For locally hosted Qwen/DeepSeek via SGLang
        vllm_url = settings.SGLANG_ENDPOINT
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": settings.QWEN_35_2B_INSTRUCT, # Change to your loaded model
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        }
        res = requests.post(vllm_url, headers=headers, json=payload)
        return res.json()["choices"][0]["message"]["content"] 
    return "Error: Invalid Provider."



# --- 2. DYNAMIC LLM ROUTER ---
def get_llm(provider: str):
    """Dynamically routes to the chosen LLM backend."""
    if provider == "gemini":
        #return ChatGoogleGenerativeAI(
        #    model="gemini-1.5-pro", 
        #    temperature=0, 
        #    google_api_key=settings.GEMINI_API_KEY
        #)
        gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
        return gemini_client
    elif provider == "sglang":
        # SGLang provides an OpenAI-compatible API layer
        return ChatOpenAI(
            model="qwen", # Use the generic name configured in SGLang
            temperature=0,
            api_key="EMPTY", # Local models don't need a real key
            base_url="http://sglang:30000/v1" # Point to the internal Docker container
        )
    else: # Default to OpenAI
        return ChatOpenAI(
            model="gpt-4o", 
            temperature=0, 
            api_key=settings.OPENAI_API_KEY
        )

