import aiohttp
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from pydantic import BaseModel

class ScraperResult(BaseModel):
    name: str
    confidence: float
    source: str
    raw_data: Dict[str, Any]

class BaseScraper(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def scrape(self, phone: str) -> Optional[ScraperResult]:
        pass

class TruecallerScraper(BaseScraper):
    def __init__(self, api_key: str = None, mock_mode: bool = False):
        super().__init__("truecaller")
        self.api_key = api_key
        self.mock_mode = mock_mode
        self.base_url = "https://search5-noneu.truecaller.com/v2/search"

    async def scrape(self, phone: str) -> Optional[ScraperResult]:
        if self.mock_mode:
            return ScraperResult(
                name="Ahmed Khan (Mock)",
                confidence=0.9,
                source=self.name,
                raw_data={"phone": phone, "name": "Ahmed Khan", "type": "Person"}
            )
        
        if not self.api_key:
            return None
        
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "User-Agent": "Truecaller/11.75.5 (Android;11)"
            }
            params = {
                "q": phone,
                "type": "4"
            }
            try:
                async with session.get(self.base_url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('results'):
                            result = data['results'][0]
                            return ScraperResult(
                                name=f"{result.get('firstName', '')} {result.get('lastName', '')}".strip(),
                                confidence=0.8,
                                source=self.name,
                                raw_data=result
                            )
            except Exception as e:
                print(f"Truecaller error: {e}")
        return None

class WhitepagesScraper(BaseScraper):
    def __init__(self):
        super().__init__("whitepages")

    async def scrape(self, phone: str) -> Optional[ScraperResult]:
        return None


class NumverifyScraper(BaseScraper):
    def __init__(self, api_key: str = None):
        super().__init__("numverify")
        self.api_key = api_key or "demo"  # demo key has limited requests
        self.base_url = "http://api.numverify.com"

    async def scrape(self, phone: str) -> Optional[ScraperResult]:
        if not self.api_key:
            return None
        
        # Remove + prefix for API
        phone_num = phone.lstrip('+')
        
        async with aiohttp.ClientSession() as session:
            params = {
                "number": phone_num,
                "access_key": self.api_key
            }
            try:
                async with session.get(f"{self.base_url}/php_helper_script.php", params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('valid') and data.get('carrier'):
                            name = data['carrier'].get('name', '')
                            if name:
                                return ScraperResult(
                                    name=name,
                                    confidence=0.6,
                                    source=self.name,
                                    raw_data=data
                                )
            except Exception as e:
                print(f"Numverify error: {e}")
        return None
