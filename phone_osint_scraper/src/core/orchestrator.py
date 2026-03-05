import time
import asyncio
import json
from typing import Optional, List
from src.models.clickhouse_row import ClickHouseRow
from src.core.clickhouse import ClickHouseClient
from src.core.utils import PhoneNormalizer, CountryDetector
from src.pipelines.name_finder import NameFinderPipeline
from src.pipelines.id_enricher import IDEnricher
from src.pipelines.address_enricher import AddressEnricher
from src.scrapers.name_scrapers import TruecallerScraper, WhitepagesScraper, NumverifyScraper
from src.scrapers.pakistan import PakWheelsScraper, JangScraper
from src.core.config import settings

class NameFirstOrchestrator:
    def __init__(self, clickhouse_client: ClickHouseClient):
        self.clickhouse = clickhouse_client
        self.name_finder = NameFinderPipeline([
            TruecallerScraper(settings.TRUECALLER_API_KEY, mock_mode=False),
            NumverifyScraper(settings.NUMVERIFY_API_KEY),
            WhitepagesScraper(),
            PakWheelsScraper(),
            JangScraper()
        ])
        self.id_enricher = IDEnricher()
        self.address_enricher = AddressEnricher()

    async def process_phone(self, phone: str) -> str:
        start_time = time.time()
        normalized = PhoneNormalizer.normalize(phone)
        country = CountryDetector.detect(normalized)
        
        # STEP 1: MANDATORY - Find name
        name_result = await self.name_finder.find_name(normalized)
        
        if not name_result:
            # Early exit - store failed attempt
            row = ClickHouseRow(
                phone=normalized,
                owner_name="",
                owner_name_confidence=0.0,
                country=country,
                status="failed",
                raw_json=json.dumps({"error": "No name found"}),
                pipeline_duration=int((time.time() - start_time) * 1000)
            )
            self.clickhouse.insert([row])
            return "failed-no-name"
        
        # STEP 2: ENRICH with name
        enrichment_tasks = [
            self.id_enricher.enrich(normalized, name_result.name, country),
            self.address_enricher.enrich(normalized, name_result.name),
        ]
        enrichments = await asyncio.gather(*enrichment_tasks)
        id_enrichment = enrichments[0]
        addr_enrichment = enrichments[1]
        
        # STEP 3: Store everything
        row = ClickHouseRow(
            phone=normalized,
            owner_name=name_result.name,
            owner_name_confidence=name_result.confidence,
            cnic=id_enrichment.cnic,
            passport=id_enrichment.passport,
            address=addr_enrichment.address,
            country=country,
            companies=id_enrichment.companies,
            sources=[name_result.source],
            raw_json=json.dumps(name_result.raw_data),
            status="success" if name_result.confidence > 0.7 else "partial",
            pipeline_duration=int((time.time() - start_time) * 1000)
        )
        self.clickhouse.insert([row])
        
        return row.status
