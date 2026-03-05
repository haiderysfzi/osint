import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    CLICKHOUSE_HOST: str = os.getenv("CLICKHOUSE_HOST", "localhost")
    CLICKHOUSE_PORT: int = int(os.getenv("CLICKHOUSE_PORT", 8123))
    CLICKHOUSE_USER: str = os.getenv("CLICKHOUSE_USER", "default")
    CLICKHOUSE_PASSWORD: str = os.getenv("CLICKHOUSE_PASSWORD", "osint_password")
    CLICKHOUSE_DB: str = os.getenv("CLICKHOUSE_DB", "default")
    
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
    
    TRUECALLER_API_KEY: str = os.getenv("TRUECALLER_API_KEY", "")
    NUMVERIFY_API_KEY: str = os.getenv("NUMVERIFY_API_KEY", "")

settings = Settings()
