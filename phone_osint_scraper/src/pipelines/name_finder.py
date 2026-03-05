import asyncio
from typing import List, Optional
from src.scrapers.name_scrapers import BaseScraper, ScraperResult

class NameFinderPipeline:
    def __init__(self, scrapers: List[BaseScraper]):
        self.scrapers = scrapers

    async def find_name(self, phone: str) -> Optional[ScraperResult]:
        """Runs scrapers in parallel and selects the best name result."""
        tasks = [scraper.scrape(phone) for scraper in self.scrapers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        valid_results = [r for r in results if isinstance(r, ScraperResult) and r.name]
        if not valid_results:
            return None
        
        # Select best result by confidence
        best_result = max(valid_results, key=lambda x: x.confidence)
        return best_result
