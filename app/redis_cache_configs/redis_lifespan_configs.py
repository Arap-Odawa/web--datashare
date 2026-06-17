
from fastapi import Request, Depends

from pydantic_models.pydantic_models import (
    GeminiLLMRequestType,
    GeminiLLMCostType,

)

async def gemini_free_fast_api_manager_1(request: Request):
    manager = request.app.state.gemini_free_fast_api_manager
    
    # 1. Get the connection (validates RPM and RPD limits)
    conn = await manager.get_connection()
    
    # 2. Yield the connection to the route
    return conn


async def gemini_free_pro_api_manager_1(request: Request):
    manager = request.app.state.gemini_free_pro_api_manager
    
    # 1. Get the connection (validates RPM and RPD limits)
    conn = await manager.get_connection()
    
    # 2. Yield the connection to the route
    return conn



async def gemini_paid_fast_api_manager_1(request: Request):
    manager = request.app.state.gemini_paid_fast_api_manager
    
    # 1. Get the connection (validates RPM and RPD limits)
    conn = await manager.get_connection()
    
    # 2. Yield the connection to the route
    return conn




async def gemini_paid_pro_api_manager_1(request: Request):
    manager = request.app.state.gemini_paid_pro_api_manager
    
    # 1. Get the connection (validates RPM and RPD limits)
    conn = await manager.get_connection()
    
    # 2. Yield the connection to the route
    return conn


async def gemini_api_key_rotate_final_selection(request:Request,fast_or_pro:str,paid_or_free:str):
    if fast_or_pro == GeminiLLMCostType.FREE and paid_or_free == GeminiLLMRequestType.FAST:
        conn1 = await gemini_free_fast_api_manager_1(request=request)
        return conn1

    elif fast_or_pro == GeminiLLMCostType.FREE and paid_or_free == GeminiLLMRequestType.PRO:
        conn1 = await gemini_free_pro_api_manager_1(request=request)
        return conn1
    
    elif fast_or_pro == GeminiLLMCostType.PAID and paid_or_free == GeminiLLMRequestType.FAST:
        conn1 = await gemini_paid_fast_api_manager_1(request=request)
        return conn1

    elif fast_or_pro == GeminiLLMCostType.PAID and paid_or_free == GeminiLLMRequestType.PRO:
        conn1 = await gemini_paid_pro_api_manager_1(request=request)
        return conn1



