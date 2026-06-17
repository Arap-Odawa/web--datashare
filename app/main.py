import polars as pl
import uvicorn,secrets, asyncio, datetime, sys
import base64
import hashlib
from datetime import datetime as datetime_c
from fastapi.middleware.wsgi import WSGIMiddleware
from fastapi import Depends, FastAPI, Request, HTTPException, status, APIRouter
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from contextlib import asynccontextmanager
import redis.asyncio as aioredis

from loguru import logger
from pathlib import Path # Imported pathlib

from prometheus_fastapi_instrumentator import Instrumentator

from drm_viz.data_review_viz import data_review_dash_app
from trends_viz.data_trends_viz import data_trends_dash_app
from configs.loguru_configs import rotator
from configs.util_configs import get_settings
from api_router import router

from llm_logic.llm_gemini_api_key_rotate import (
    GeminiFreeFastRedisRotatingAPIKeyManagerSync,
    GeminiFreeProRedisRotatingAPIKeyManagerSync,
    GeminiPaidFastRedisRotatingAPIKeyManagerSync,
    GeminiPaidProRedisRotatingAPIKeyManagerSync,

)

from redis_cache_configs.redis_cache_configs import gemini_redis_cache_keys
from llm_logic.llm_logs_db import DBManager

settings = get_settings()
import logging

class InterceptHandler(logging.Handler):
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

# Route standard python logging through loguru
logging.basicConfig(handlers=[InterceptHandler()], level=logging.INFO, force=True)

logger.remove()
logger.add(sys.stderr, format="{extra} | {time:MMMM D, YYYY @ HH:mm:ss} | {level} | {message}", enqueue=True)
logger = logger.bind(CurrentParticularAPI="NYM-Web-DataShare")

stamp_today = datetime_c.now()
today = stamp_today.strftime("%Y%m%d")
path_log = "./loguru_logs/nym_web_datashare_backlogs_{}.log".format(today)
logger.add(path_log, 
           serialize=True,
           encoding='utf-8', 
           rotation=rotator.should_rotate,
           level="INFO", 
#           format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message} | {extra}",
#           format="{CurrentParticularAPI} | {time:YYYY-MM-DD HH:mm:ss} | {level} | {message} | {extra}",
           compression="zip",
           enqueue=True, 
           diagnose=True)


logger.add(sys.stdout, level="INFO")

logger.debug(path_log)




@asynccontextmanager
async def lifespan(app: FastAPI):

    # Initialise the Redis database.
    gemini_redis_cache_keys1=await gemini_redis_cache_keys()
    app.state.gemini_redis_cache_keys1 = gemini_redis_cache_keys1
    
    # Initialize the PostgreSQL connection pool.
    await DBManager.init_pool(settings)
    
    # Initialize the Redis-backed manager
    gemini_free_fast_api_manager = GeminiFreeFastRedisRotatingAPIKeyManagerSync()
    check1=await gemini_free_fast_api_manager.initialize()
    
    app.state.gemini_free_fast_api_manager = check1

    gemini_free_pro_api_manager = GeminiFreeProRedisRotatingAPIKeyManagerSync()
    check11=await gemini_free_pro_api_manager.initialize()
    
    app.state.gemini_free_pro_api_manager = check11

    gemini_paid_fast_api_manager = GeminiPaidFastRedisRotatingAPIKeyManagerSync()
    check111=await gemini_paid_fast_api_manager.initialize()
    
    app.state.gemini_paid_fast_api_manager = check111

    gemini_paid_pro_api_manager = GeminiPaidProRedisRotatingAPIKeyManagerSync()
    check1111=await gemini_paid_pro_api_manager.initialize()
    
    app.state.gemini_paid_pro_api_manager = check1111
        
        

    yield
    await gemini_free_fast_api_manager.close()
    await gemini_free_pro_api_manager.close()
    await gemini_paid_fast_api_manager.close()
    await gemini_paid_pro_api_manager.close()

    # Close the PostgreSQL connection pool.
    await DBManager.close_pool()

    await app.state.gemini_redis_cache_keys1.__aexit__()



# 1. FASTAPI SERVER SETUP ---
#fastapi_app = FastAPI()



fastapi_app = FastAPI(
    lifespan=lifespan,
    #openapi_url="/v1/achiel/openapi.json",
    #openapi_url=f"{settings.ACTIVE_API_STR}/b0e7893b0c39426258b11a88798c438/zeeechat/openapi.json",
    #docs_url= f"/b0e7893b0c39426258b11a88798c438/zeeechat/zeeeng_api_documentation",
    redoc_url=None,


    docs_url=None,
    openapi_url=None,
    title=settings.PROJECT_NAME,
    description="API Documentation for the NYM Web DataShare",
    summary="This is a compendium of all the API Documentations for all the API endpoints that are critical to the working of the NYM Web DataShare.",
    version=settings.PROJECT_VERSION,
    contact={
        "Name": "Michael Odawa - Odwizzle",
        "Email": "modawa@path.org",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },    
)



fastapi_app.mount("/data-review-meeting-visuals", WSGIMiddleware(data_review_dash_app.server))

fastapi_app.mount("/data-trends-dashboard", WSGIMiddleware(data_trends_dash_app.server))


# 2. Instrument the FastAPI app for Prometheus metrics
Instrumentator().instrument(fastapi_app).expose(fastapi_app)


@fastapi_app.get("/")
def index(request: Request):
    # Enforce simple authentication, returning HTTP 500 on failure
    check_base_url_auth(request)

    return {
        "message": "API Active. Visit /data-review-meeting-visuals/", 
        "status": "healthy", 
        "service": "Data Review Meeting Visuals App",
        "extra_dashboards": {
            "grafana_dashboard": "/grafana/ (access via dashboards entrypoint on port 8085)",
            "prometheus_dashboard": "/prometheus/ (access via dashboards entrypoint on port 8085)",
            "traefik_dashboard": "/dashboard/ (access via dashboards entrypoint on port 8085)",
            "free_llm_api_dashboard": "/free-llm-api/ (access via dashboards entrypoint on port 8085)",
            "fastapi_swagger_docs": f"/{settings.ACTIVE_API_STR}/{settings.DOCS_OBFUSCATE}/nym-viz/web-datashare-open-apidocumentation (access via port 8045)",
            "fastapi_redoc_docs": f"/{settings.ACTIVE_API_STR}/{settings.DOCS_OBFUSCATE}/nym-viz/redoc/web-datashare-documentation (access via port 8045)"
        }
    }



# ---------------------------------------------------------------------------
# DDoS RATE LIMIT MIDDLEWARE (Application Layer — backs the Traefik layer)
# Enforces a sliding-window limit of 10 requests / 60 seconds per client IP.
# Uses Redis DB 2 (separate from cache DBs 0 & 1) to avoid key collisions.
# The real client IP is read from the X-Forwarded-For header which Traefik
# injects automatically when uvicorn is started with proxy_headers=True.
# On breach, returns HTTP 429 Too Many Requests with Retry-After: 60.
# ---------------------------------------------------------------------------
class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Sliding-window IP-based rate limiter backed by Redis.
    Limit: RATE_LIMIT_MAX_REQUESTS requests per RATE_LIMIT_WINDOW_SECONDS.
    """
    RATE_LIMIT_MAX_REQUESTS: int = settings.RATELIMIT_RPM
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    REDIS_DB: int = 2  # Dedicated DB to avoid collision with app caches.

    async def _get_redis(self) -> aioredis.Redis:
        """Create a short-lived async Redis client for this request."""
        _settings = get_settings()
        # Replace DB index in the URL (e.g. redis://redis:6379/0 -> /2)
        base_url = _settings.REDIS_URL.rsplit("/", 1)[0]
        return aioredis.from_url(
            f"{base_url}/{self.REDIS_DB}",
            encoding="utf-8",
            decode_responses=True,
        )

    def _get_client_ip(self, request: Request) -> str:
        """Extract the real client IP from X-Forwarded-For or fall back to socket."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first (leftmost) IP — the originating client.
            return forwarded_for.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "unknown"

    async def dispatch(self, request: Request, call_next):
        client_ip = self._get_client_ip(request)
        rate_key = f"rate_limit:{client_ip}"
        r = await self._get_redis()
        try:
            pipe = r.pipeline()
            pipe.incr(rate_key)
            pipe.expire(rate_key, self.RATE_LIMIT_WINDOW_SECONDS)
            results = await pipe.execute()
            request_count = results[0]
        finally:
            await r.aclose()

        if request_count > self.RATE_LIMIT_MAX_REQUESTS:
            logger.warning(
                f"[RateLimit] IP {client_ip} exceeded {self.RATE_LIMIT_MAX_REQUESTS} req/"
                f"{self.RATE_LIMIT_WINDOW_SECONDS}s limit (count={request_count}). "
                f"Returning HTTP 429."
            )
            return Response(
                content='{"detail":"Too Many Requests — rate limit exceeded. Retry after 60 seconds."}',
                status_code=429,
                media_type="application/json",
                headers={"Retry-After": str(self.RATE_LIMIT_WINDOW_SECONDS)},
            )
        return await call_next(request)


# Register RateLimitMiddleware BEFORE CORS so it intercepts all requests,
# including those proxied to the WSGI-mounted Dash sub-apps.
fastapi_app.add_middleware(RateLimitMiddleware)

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


fastapi_app.include_router(router)

security = HTTPBasic()


def verify_hashed_password(plain_password: str, hashed_password: str) -> bool:
    if hashed_password.startswith("{SHA}"):
        sha1_hash = hashlib.sha1(plain_password.encode('utf-8')).digest()
        encoded = "{SHA}" + base64.b64encode(sha1_hash).decode('utf-8')
        return secrets.compare_digest(encoded, hashed_password)
    return secrets.compare_digest(plain_password, hashed_password)


def check_base_url_auth(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication required"
        )
    try:
        auth_type, credentials = auth_header.split(" ", 1)
        if auth_type.lower() != "basic":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Invalid authentication scheme"
            )
        decoded = base64.b64decode(credentials).decode("utf-8")
        username, password = decoded.split(":", 1)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid authorization header structure"
        )

    correct_username = secrets.compare_digest(username, settings.DASHBOARDS_USERNAME)
    correct_password = verify_hashed_password(password, settings.HASHED_PASSWORD_2)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unauthorized"
        )


def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, settings.DASHBOARDS_USERNAME)
    correct_password = verify_hashed_password(credentials.password, settings.HASHED_PASSWORD_2)
    if not (correct_username and correct_password):
        child_logger = logger.bind(username=credentials.username,)
        child_logger.warning(f"User '{credentials.username}' running on IP address: 'blanked' has attempted to access the documentation pages of the Zeeeng Services at {datetime.datetime.now()}.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@fastapi_app.get(f"/{settings.ACTIVE_API_STR}/{settings.DOCS_OBFUSCATE}/nym-viz/web-datashare-open-apidocumentation", include_in_schema=False)
async def get_swagger_documentation(username: str = Depends(get_current_username)):
    logger.error(f"Access to NYM Web DataShare API Documentation (docs endpoint) by {username} at {datetime.datetime.now()}")
    return get_swagger_ui_html(openapi_url=f"{settings.ACTIVE_API_STR}/{settings.DOCS_OBFUSCATE}/nym-viz/openapi.json", title="ZeeeChat API Documentations")
    #return get_swagger_ui_html(openapi_url="/docs/openapi.json", title="ZeeeChat API Documentations")


@fastapi_app.get(f"/{settings.ACTIVE_API_STR}/{settings.DOCS_OBFUSCATE}/nym-viz/redoc/web-datashare-documentation", include_in_schema=False)
async def get_redoc_documentation(username: str = Depends(get_current_username)):
    logger.error(f"Access to NYM Web DataShare API Documentation (redocs endpoint) by {username} at {datetime.datetime.now()}")
    return get_redoc_html(openapi_url=f"{settings.ACTIVE_API_STR}/{settings.DOCS_OBFUSCATE}/nym-viz/openapi.json", title="ZeeeChat API Documentations")


@fastapi_app.get(f"/{settings.ACTIVE_API_STR}/{settings.DOCS_OBFUSCATE}/nym-viz/openapi.json", include_in_schema=False)
async def openapi(username: str = Depends(get_current_username)):
    logger.error(f"Access to NYM Web DataShare API Documentation (OpenAPI endpoint) by {username} at {datetime.datetime.now()}")
    return get_openapi(title=fastapi_app.title, version=fastapi_app.version, routes=fastapi_app.routes)





if __name__ == "__main__":
    uvicorn.run(fastapi_app, host="0.0.0.0", port=settings.DEFAULT_PORT, proxy_headers=True,forwarded_allow_ips="*")




"""


if __name__ == "__main__":

    reload1=settings.ENV_PROD_DEV
        

    if reload1=="PROD":
        async def run_server():
            config = uvicorn.Config(
                #"main:fastapi_app",
                "fastapi_app",
                host=settings.DOMAIN_PORTLESS_PROD,
                port=settings.DEFAULT_PORT,
                #workers=settings.NUM_WEB_VIZ_WORKERS_PROD,
                log_level="info",
                proxy_headers=True,
                reload=False,
            )
            server = uvicorn.Server(config)
            await server.serve()

        asyncio.run(run_server())



    elif reload1=="DEV":        
        async def run_server():
            config = uvicorn.Config(
                #"main:fastapi_app",
                "fastapi_app",
                host=settings.DOMAIN_PORTLESS_DEV,
                port=settings.DEFAULT_PORT,
                #workers=settings.NUM_WEB_VIZ_WORKERS_DEV,
                log_level="info",
                proxy_headers=True,
                reload=True,
            )
            server = uvicorn.Server(config)
            await server.serve()

        asyncio.run(run_server())


"""

