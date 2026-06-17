from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

from decouple import config 
import time


class Settings(BaseSettings):

    DAILY_MINUTES: int = 86400

    GRAFANA_PASSWORD: str = config("GRAFANA_PASSWORD", cast=str) 

    GRAFANA_USERNAME: str = config("GRAFANA_USERNAME", cast=str)

    RATELIMIT_RPM: int = config("RATELIMIT_RPM", cast=int) 
    
    RATELIMIT_RPM_BURST: int = config("RATELIMIT_RPM_BURST", cast=int) 

    RATELIMIT_PERIOD: str = config("RATELIMIT_PERIOD", cast=str)

    DASHBOARD_CREDENTIALS: str = config("DASHBOARD_CREDENTIALS", cast=str, default="") 

    DASHBOARDS_USERNAME: str = config("DASHBOARDS_USERNAME", cast=str) 

    HASHED_PASSWORD: str = config("HASHED_PASSWORD", cast=str) 

    DEFAULT_FY: int = config("DEFAULT_FY", cast=int) 

    DEFAULT_QUARTER: str = config("DEFAULT_QUARTER", cast=str)

    DEFAULT_PORT: int = config("DEFAULT_PORT", cast=int) 

    ENV_PROD_DEV: str = config("ENV_PROD_DEV", cast=str)

    DOMAIN_PORTLESS_PROD: str = config("DOMAIN_PORTLESS_PROD", cast=str)

    DOMAIN_PORTLESS_DEV: str = config("DOMAIN_PORTLESS_DEV", cast=str)

    DOMAIN_CHAT_PORTLESS_DEV: str = config("DOMAIN_CHAT_PORTLESS_DEV", cast=str)

    NUM_WEB_VIZ_WORKERS_PROD: int = config("NUM_WEB_VIZ_WORKERS_PROD", cast=int) 

    NUM_WEB_VIZ_WORKERS_DEV: int = config("NUM_WEB_VIZ_WORKERS_DEV", cast=int) 

    ACTIVE_API_STR: str = config("ACTIVE_API_STR", cast=str)

    DOCS_OBFUSCATE: str = config("DOCS_OBFUSCATE", cast=str)

    PROJECT_NAME: str = config("PROJECT_NAME", cast=str)

    PROJECT_VERSION: str = config("PROJECT_VERSION", cast=str)

    REDIS_URL: str = config("REDIS_URL", cast=str)

    REDIS_URL_1: str = config("REDIS_URL_1", cast=str)

    REDIS_CACHE_PERIOD: int = config("REDIS_CACHE_PERIOD", cast=int) 

    OPENAI_API_KEY: str = config("OPENAI_API_KEY", cast=str)

    ANTHROPIC_API_KEY: str = config("ANTHROPIC_API_KEY", cast=str)


    GEMINI_API_KEY: str = config("GEMINI_API_KEY", cast=str)

    GEMINI_API_KEY_ELEMI: str = config("GEMINI_API_KEY_ELEMI", cast=str)

    GEMINI_API_KEY_ODAWQWA: str = config("GEMINI_API_KEY_ODAWQWA", cast=str)

    GEMINI_API_KEY_JACKIES: str = config("GEMINI_API_KEY_JACKIES", cast=str)

    GEMINI_API_KEY_ZANZOTTO: str = config("GEMINI_API_KEY_ZANZOTTO", cast=str)

    GEMINI_API_KEY_PAULMWANIKI856: str = config("GEMINI_API_KEY_PAULMWANIKI856", cast=str)

    GEMINI_API_KEY_AZIMKIMINVESTMENTSLTD: str = config("GEMINI_API_KEY_AZIMKIMINVESTMENTSLTD", cast=str)

    GEMINI_API_KEY_MICHAEL_ODHIAMBO8799987: str = config("GEMINI_API_KEY_MICHAEL_ODHIAMBO8799987", cast=str)

    GEMINI_API_KEY_MICHAEL_OTIENO_ODHIAMBO89: str = config("GEMINI_API_KEY_MICHAEL_OTIENO_ODHIAMBO89", cast=str)



    GEMINI_API_KEY_PAID: str = config("GEMINI_API_KEY_PAID", cast=str)

    GEMINI_API_KEY_ELEMI_PAID: str = config("GEMINI_API_KEY_ELEMI_PAID", cast=str)

    GEMINI_API_KEY_ODAWQWA_PAID: str = config("GEMINI_API_KEY_ODAWQWA_PAID", cast=str)

    GEMINI_API_KEY_JACKIES_PAID: str = config("GEMINI_API_KEY_JACKIES_PAID", cast=str)

    GEMINI_API_KEY_ZANZOTTO_PAID: str = config("GEMINI_API_KEY_ZANZOTTO_PAID", cast=str)

    GEMINI_API_KEY_PAULMWANIKI856_PAID: str = config("GEMINI_API_KEY_PAULMWANIKI856_PAID", cast=str)

    GEMINI_API_KEY_AZIMKIMINVESTMENTSLTD_PAID: str = config("GEMINI_API_KEY_AZIMKIMINVESTMENTSLTD_PAID", cast=str)

    GEMINI_API_KEY_MICHAEL_ODHIAMBO8799987_PAID: str = config("GEMINI_API_KEY_MICHAEL_ODHIAMBO8799987_PAID", cast=str)

    GEMINI_API_KEY_MICHAEL_OTIENO_ODHIAMBO89_PAID: str = config("GEMINI_API_KEY_MICHAEL_OTIENO_ODHIAMBO89_PAID", cast=str)




    GEMINI_FREE_3_PRO_RATELIMITS_RPM: str = config("GEMINI_FREE_3_PRO_RATELIMITS_RPM", cast=str)

    GEMINI_FREE_3_PRO_RATELIMITS_RPD: str = config("GEMINI_FREE_3_PRO_RATELIMITS_RPD", cast=str)

    GEMINI_FREE_3_PRO_RATELIMITS_TPM: str = config("GEMINI_FREE_3_PRO_RATELIMITS_TPM", cast=str)

    GEMINI_FREE_3_FAST_RATELIMITS_RPM: str = config("GEMINI_FREE_3_FAST_RATELIMITS_RPM", cast=str)

    GEMINI_FREE_3_FAST_RATELIMITS_RPD: str = config("GEMINI_FREE_3_FAST_RATELIMITS_RPD", cast=str)

    GEMINI_FREE_3_FAST_RATELIMITS_TPM: str = config("GEMINI_FREE_3_FAST_RATELIMITS_TPM", cast=str)

    GEMINI_PAID_3_PRO_RATELIMITS_RPM: str = config("GEMINI_PAID_3_PRO_RATELIMITS_RPM", cast=str)

    GEMINI_PAID_3_PRO_RATELIMITS_RPD: str = config("GEMINI_PAID_3_PRO_RATELIMITS_RPD", cast=str)

    GEMINI_PAID_3_PRO_RATELIMITS_TPM: str = config("GEMINI_PAID_3_PRO_RATELIMITS_TPM", cast=str)

    GEMINI_PAID_3_FAST_RATELIMITS_RPM: str = config("GEMINI_PAID_3_FAST_RATELIMITS_RPM", cast=str)

    GEMINI_PAID_3_FAST_RATELIMITS_RPD: str = config("GEMINI_PAID_3_FAST_RATELIMITS_RPD", cast=str)

    GEMINI_PAID_3_FAST_RATELIMITS_TPM: str = config("GEMINI_PAID_3_FAST_RATELIMITS_TPM", cast=str)



    VLLM_ENDPOINT: str = config("VLLM_ENDPOINT", cast=str)

    SGLANG_ENDPOINT: str = config("SGLANG_ENDPOINT", cast=str)



    # Change this default llm when local hosting is enabled. 21032026.

    DEFAULT_LLM: str = config("GEMINI_MODEL_3_FLASH_PREVIEW", cast=str)



    OPENAI_MODEL_GPT40: str = config("OPENAI_MODEL_GPT40", cast=str)

    CLAUDE_MODEL_OPUS_46: str = config("CLAUDE_MODEL_OPUS_46", cast=str)

    CLAUDE_MODEL_OPUS_45: str = config("CLAUDE_MODEL_OPUS_45", cast=str)

    GEMINI_MODEL_3_PRO_PREVIEW: str = config("GEMINI_MODEL_3_PRO_PREVIEW", cast=str)

    GEMINI_MODEL_3_FLASH_PREVIEW: str = config("GEMINI_MODEL_3_FLASH_PREVIEW", cast=str)

    GEMINI_MODEL_25_FLASH_LITE: str = config("GEMINI_MODEL_25_FLASH_LITE", cast=str)

    GEMINI_MODEL_3_PRO_IMAGE_PREVIEW: str = config("GEMINI_MODEL_3_PRO_IMAGE_PREVIEW", cast=str)

    QWEN_25_7B_INSTRUCT: str = config("QWEN_25_7B_INSTRUCT", cast=str)

    QWEN_35_4B_INSTRUCT: str = config("QWEN_35_4B_INSTRUCT", cast=str)

    QWEN_35_2B_INSTRUCT: str = config("QWEN_35_2B_INSTRUCT", cast=str)

    QWEN_3VL_EMBEDDING_MODEL: str = config("QWEN_3VL_EMBEDDING_MODEL", cast=str)

    FREE_LLM_API_ENDPOINT: str = config("FREE_LLM_API_ENDPOINT", cast=str, default="")

    UNIFIED_API_KEY: str = config("UNIFIED_API_KEY", cast=str, default="")

    POSTGRES_HOST: str = config("POSTGRES_HOST", cast=str, default="db-postgres")
    POSTGRES_PORT: int = config("POSTGRES_PORT", cast=int, default=5432)
    POSTGRES_DB: str = config("POSTGRES_DB", cast=str, default="nym_chat_db")
    POSTGRES_USER: str = config("POSTGRES_USER", cast=str, default="nym_chat_user")
    POSTGRES_PASSWORD: str = config("POSTGRES_PASSWORD", cast=str, default="nym_chat_pass")

    class Config:
        env_file: str = ".env"


    @property
    def gemini_api_keys(self) -> list[str]:
        """Groups the keys into a list for easy rotation."""
        return [
            self.GEMINI_API_KEY_ELEMI,
            self.GEMINI_API_KEY_ODAWQWA,
            self.GEMINI_API_KEY_JACKIES,
            self.GEMINI_API_KEY_ZANZOTTO,
            self.GEMINI_API_KEY_PAULMWANIKI856,
            self.GEMINI_API_KEY_AZIMKIMINVESTMENTSLTD,
            self.GEMINI_API_KEY_MICHAEL_ODHIAMBO8799987,
            self.GEMINI_API_KEY_MICHAEL_OTIENO_ODHIAMBO89,
        ]

    @property
    def gemini_paid_api_keys(self) -> list[str]:
        """Groups the keys into a list for easy rotation."""
        return [
            self.GEMINI_API_KEY_ELEMI_PAID,
            self.GEMINI_API_KEY_ODAWQWA_PAID,
            self.GEMINI_API_KEY_JACKIES_PAID,
            self.GEMINI_API_KEY_ZANZOTTO_PAID,
            self.GEMINI_API_KEY_PAULMWANIKI856_PAID,
            self.GEMINI_API_KEY_AZIMKIMINVESTMENTSLTD_PAID,
            self.GEMINI_API_KEY_MICHAEL_ODHIAMBO8799987_PAID,
            self.GEMINI_API_KEY_MICHAEL_OTIENO_ODHIAMBO89_PAID,
        ]

    # This tells Pydantic to read from a .env file
    #model_config = SettingsConfigDict(env_file=".env")



#############################################
# TIMED_LRU_CACHE for global settings so that the settings are refreshed every 6 hours to pick up any 
# changes made to .env and reloaded every 6 hours/ 25000 seconds. The timed_lru_cache is defined here
# using hardcoded defaults to avoid cyclical reference of the settings. Incase it is required to change
# the defaults i.e. ttl and maxsize, these can be done manually. 05032025.
##################################


def timed_global_settings_lru_cache(ttl=25000):
    def wrapper_cache(func):
        @lru_cache(maxsize=20)
        def wrapped_func(*args, **kwargs):
            now = time.time()
            result, last_update = wrapped_func.cache_info().hits, wrapped_func.cache_info().currsize
            if result > 0 and now - last_update > ttl:
                wrapped_func.cache_clear()
            return func(*args, **kwargs)
        return wrapped_func
    return wrapper_cache



#@lru_cache(maxsize=6000)
@timed_global_settings_lru_cache()
def get_settings() -> Settings:
    return Settings()

