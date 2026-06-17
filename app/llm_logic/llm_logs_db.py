import psycopg
from psycopg_pool import AsyncConnectionPool
import asyncio
import logging
from typing import Optional
from pydantic_models.pydantic_models import LLMChatLog

logger = logging.getLogger("chat_app")

class DBManager:
    pool: Optional[AsyncConnectionPool] = None

    @classmethod
    async def init_pool(cls, settings):
        from configs.prometheus_metrics import monitor_function
        with monitor_function("database_writes", "db_init_pool"):
            conn_str = (
                f"host={settings.POSTGRES_HOST} "
                f"port={settings.POSTGRES_PORT} "
                f"dbname={settings.POSTGRES_DB} "
                f"user={settings.POSTGRES_USER} "
                f"password={settings.POSTGRES_PASSWORD}"
            )
            # Try to connect with retries to handle database startup delays
            for i in range(15):
                try:
                    # Test connection first
                    async with await psycopg.AsyncConnection.connect(conn_str, connect_timeout=3) as conn:
                        # Create table
                        async with conn.cursor() as cur:
                            await cur.execute("""
                                CREATE TABLE IF NOT EXISTS llm_chat_logs (
                                    id SERIAL PRIMARY KEY,
                                    query_id UUID UNIQUE,
                                    thread_id VARCHAR(255) NOT NULL,
                                    provider VARCHAR(50) NOT NULL,
                                    user_prompt TEXT NOT NULL,
                                    extraction_prompt_response TEXT,
                                    insights_prompt_response TEXT,
                                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                                );
                                ALTER TABLE llm_chat_logs ADD COLUMN IF NOT EXISTS query_id UUID UNIQUE;
                            """)
                        logger.info("Successfully connected to PostgreSQL and validated tables.")
                        break
                except Exception as e:
                    logger.warning(f"Database connection attempt {i+1} failed: {e}. Retrying in 2 seconds...")
                    await asyncio.sleep(2)
            else:
                logger.error("Failed to connect to the database after 15 attempts.")
                raise RuntimeError("Database connection failed")

            cls.pool = AsyncConnectionPool(conninfo=conn_str, open=True, min_size=1, max_size=10)

    @classmethod
    async def close_pool(cls):
        if cls.pool:
            await cls.pool.close()
            cls.pool = None
            logger.info("PostgreSQL connection pool closed.")

    @classmethod
    async def log_interaction_model(cls, log_entry: LLMChatLog):
        from configs.prometheus_metrics import monitor_function
        with monitor_function("database_writes", "db_log_interaction_model"):
            if not cls.pool:
                logger.error("Database pool not initialized. Cannot log interaction.")
                return
            
            try:
                async with cls.pool.connection() as conn:
                    async with conn.cursor() as cur:
                        await cur.execute(
                            """
                            INSERT INTO llm_chat_logs 
                            (query_id, thread_id, provider, user_prompt, extraction_prompt_response, insights_prompt_response)
                            VALUES (%s, %s, %s, %s, %s, %s);
                            """,
                            (
                                log_entry.query_id,
                                log_entry.thread_id,
                                log_entry.provider,
                                log_entry.user_prompt,
                                log_entry.extraction_prompt_response,
                                log_entry.insights_prompt_response
                            )
                        )
                logger.info(f"Logged LLM interaction for thread {log_entry.thread_id} to database.")
            except Exception as e:
                logger.error(f"Error logging LLM interaction to database: {e}")
