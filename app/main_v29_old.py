import polars as pl
import uvicorn,secrets, asyncio, datetime, sys
from datetime import datetime as datetime_c
from fastapi.middleware.wsgi import WSGIMiddleware
from fastapi import Depends, FastAPI, Request, HTTPException, status, APIRouter
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware

from loguru import logger
from pathlib import Path # Imported pathlib

from prometheus_fastapi_instrumentator import Instrumentator

from drm_viz.data_review_viz import data_review_dash_app
from trends_viz.data_trends_viz import data_trends_dash_app
from configs.loguru_configs import rotator
from configs.util_configs import get_settings
from api_router import router

settings = get_settings()


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




# 1. FASTAPI SERVER SETUP ---
#fastapi_app = FastAPI()



fastapi_app = FastAPI(
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
def index():
    return {"message": "API Active. Visit /data-review-meeting-visuals/", "status": "healthy", "service": "Data Review Meeting Visuals App"}



fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


fastapi_app.include_router(router)

security = HTTPBasic()


def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, settings.DASHBOARDS_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, settings.HASHED_PASSWORD)
    if not (correct_username and correct_password):
        child_logger = logger.bind(username=credentials.username,)
        child_logger.warning(f"User '{credentials.username}' running on IP address: 'blanked' has attempted to access the documentation pages of the Zeeeng Services at {datetime.now()}.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@fastapi_app.get(f"/{settings.ACTIVE_API_STR}/{settings.DOCS_OBFUSCATE}/nym-viz/web-datashare-open-apidocumentation", include_in_schema=False)
async def get_swagger_documentation(username: str = Depends(get_current_username)):
    logger.error(f"Access to NYM Web DataShare API Documentation (docs endpoint) by {username} at {datetime.now()}")
    return get_swagger_ui_html(openapi_url=f"{settings.ACTIVE_API_STR}/{settings.DOCS_OBFUSCATE}/nym-viz/openapi.json", title="ZeeeChat API Documentations")


@fastapi_app.get(f"/{settings.ACTIVE_API_STR}/{settings.DOCS_OBFUSCATE}/nym-viz/redoc/web-datashare-documentation", include_in_schema=False)
async def get_redoc_documentation(username: str = Depends(get_current_username)):
    logger.error(f"Access to NYM Web DataShare API Documentation (redocs endpoint) by {username} at {datetime.now()}")
    return get_redoc_html(openapi_url=f"{settings.ACTIVE_API_STR}/{settings.DOCS_OBFUSCATE}/nym-viz/openapi.json", title="ZeeeChat API Documentations")


@fastapi_app.get(f"/{settings.ACTIVE_API_STR}/{settings.DOCS_OBFUSCATE}/nym-viz/openapi.json", include_in_schema=False)
async def openapi(username: str = Depends(get_current_username)):
    logger.error(f"Access to NYM Web DataShare API Documentation (OpenAPI endpoint) by {username} at {datetime.now()}")
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

