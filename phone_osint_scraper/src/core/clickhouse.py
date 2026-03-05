import clickhouse_connect
from typing import List, Optional
import pandas as pd
from src.models.clickhouse_row import ClickHouseRow
from src.core.config import settings

class ClickHouseClient:
    def __init__(self, host: str = None, port: int = None, user: str = None, password: str = None, database: str = None):
        self.client = clickhouse_connect.get_client(
            host=host or settings.CLICKHOUSE_HOST,
            port=port or settings.CLICKHOUSE_PORT,
            username=user or settings.CLICKHOUSE_USER,
            password=password or settings.CLICKHOUSE_PASSWORD,
            database=database or settings.CLICKHOUSE_DB
        )
    
    def insert(self, rows: List[ClickHouseRow]):
        """Batch insert rows optimized with pandas DataFrame."""
        if not rows:
            return
        
        df = ClickHouseRow.to_pandas(rows)
        self.client.insert_df(
            table='phone_osint_results',
            df=df
        )
    
    def query_recent(self, phone: str, limit: int = 1) -> pd.DataFrame:
        """Fetch the most recent lookup for a given phone number."""
        query = """
            SELECT * FROM phone_osint_results 
            WHERE phone = %(phone)s 
            ORDER BY ingested_at DESC 
            LIMIT %(limit)s
        """
        return self.client.query_df(query, {'phone': phone, 'limit': limit})

    def close(self):
        self.client.close()
