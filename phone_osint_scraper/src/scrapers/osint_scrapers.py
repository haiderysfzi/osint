import aiohttp
import asyncio
import re
import json
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from .name_scrapers import BaseScraper, ScraperResult


class GoogleDorkScraper(BaseScraper):
    """OSINT: Use Google Dorks to find phone number info - comprehensive search"""
    
    def __init__(self):
        super().__init__("google_dork")
    
    async def scrape(self, phone: str) -> Optional[ScraperResult]:
        phone_clean = phone.lstrip('+').replace(' ', '').replace('-', '')
        
        # Comprehensive dorks for finding names/owners
        dorks = [
            # Direct phone searches
            f'"{phone}"',
            f'"{phone_clean}"',
            # Social media
            f'"{phone}" site:facebook.com',
            f'"{phone}" site:twitter.com',
            f'"{phone}" site:instagram.com',
            f'"{phone}" site:linkedin.com',
            f'"{phone}" site:telegram.me',
            # Business/classifieds
            f'"{phone}" "for sale"',
            f'"{phone}" "wanted"',
            # Business directories
            f'"{phone}" "director"',
            f'"{phone}" "CEO"',
            f'"{phone}" "owner"',
            # WhatsApp/Telegram
            f'"{phone}" "WhatsApp"',
            f'"{phone}" "Telegram"',
            # CNIC/ID (Pakistan)
            f'"{phone}" "CNIC"',
            # UK
            f'"{phone}" "UK"',
        ]
        
        try:
            async with aiohttp.ClientSession(
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                }
            ) as session:
                # Try DuckDuckGo first
                for dork in dorks[:8]:
                    result = await self._search_duckduckgo(session, dork)
                    if result and result.name:
                        return result
                
                # Fallback: try Google (may get blocked)
                for dork in dork[:4]:
                    result = await self._search_bing(session, dork)
                    if result and result.name:
                        return result
                        
        except Exception as e:
            print(f"GoogleDork error: {e}")
        
        return None
    
    async def _search_duckduckgo(self, session, query: str) -> Optional[ScraperResult]:
        try:
            url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            async with session.get(url, timeout=15) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Get all result snippets
                    results = soup.select('.result__snippet')
                    if results:
                        for result in results[:3]:
                            snippet = result.get_text()
                            name = self._extract_name(snippet)
                            if name:
                                return ScraperResult(
                                    name=name,
                                    confidence=0.6,
                                    source=self.name,
                                    raw_data={"query": query, "snippet": snippet[:200]}
                                )
                        
                        # If no name found, return any useful info
                        first_result = results[0].get_text()
                        return ScraperResult(
                            name=f"Found: {first_result[:50]}",
                            confidence=0.3,
                            source=self.name,
                            raw_data={"query": query, "snippet": first_result[:200]}
                        )
        except Exception as e:
            print(f"DuckDuckGo search error: {e}")
        return None
    
    async def _search_bing(self, session, query: str) -> Optional[ScraperResult]:
        try:
            url = f"https://www.bing.com/search?q={quote_plus(query)}"
            async with session.get(url, timeout=15) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    results = soup.select('.b_caption')
                    if results:
                        snippet = results[0].get_text()
                        name = self._extract_name(snippet)
                        if name:
                            return ScraperResult(
                                name=name,
                                confidence=0.6,
                                source=self.name,
                                raw_data={"query": query, "snippet": snippet[:200]}
                            )
        except Exception as e:
            pass
        return None
    
    def _extract_name(self, text: str) -> Optional[str]:
        # Patterns for extracting names
        patterns = [
            r'([A-Z][a-z]+\s[A-Z][a-z]+)',
            r'named\s+([A-Z][a-z]+\s[A-Z][a-z]+)',
            r'owner[:\s]+([A-Z][a-z]+\s[A-Z][a-z]+)',
            r'contact[:\s]+([A-Z][a-z]+\s[A-Z][a-z]+)',
            r'person[:\s]+([A-Z][a-z]+\s[A-Z][a-z]+)',
            r'([A-Z][a-z]+)\s+[A-Z][a-z]+\s+[A-Z][a-z]+',  # First Last Middle
            r'Mr\.\s+([A-Z][a-z]+)',
            r'Mrs\.\s+([A-Z][a-z]+)',
            r'Ms\.\s+([A-Z][a-z]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return None


class CarrierLookupScraper(BaseScraper):
    """OSINT: Get carrier, line type, location using PhoneInfoga approach"""
    
    def __init__(self):
        super().__init__("carrier_lookup")
    
    async def scrape(self, phone: str) -> Optional[ScraperResult]:
        phone_clean = phone.lstrip('+')
        
        try:
            async with aiohttp.ClientSession() as session:
                # Try multiple free carrier lookup services
                result = await self._carrierlookup_api(session, phone_clean)
                if result:
                    return result
                    
                result = await self._numverify_api(session, phone_clean)
                if result:
                    return result
                    
        except Exception as e:
            print(f"Carrier lookup error: {e}")
        
        return None
    
    async def _carrierlookup_api(self, session, phone: str) -> Optional[ScraperResult]:
        try:
            url = f"https://free-carrier-lookup.p.rapidapi.com/carrier/{phone}"
            headers = {
                "X-RapidAPI-Key": "demo",
                "X-RapidAPI-Host": "free-carrier-lookup.p.rapidapi.com"
            }
            # This is a placeholder - real implementation would need API key
            # For now, use phonenumbers library for basic carrier info
            import phonenumbers
            parsed = phonenumbers.parse(f"+{phone}")
            carrier = phonenumbers.carrier.name_for_number(parsed, "en")
            if carrier:
                return ScraperResult(
                    name=f"Carrier: {carrier}",
                    confidence=0.7,
                    source=self.name,
                    raw_data={"carrier": carrier, "phone": phone}
                )
        except Exception as e:
            pass
        return None
    
    async def _numverify_api(self, session, phone: str) -> Optional[ScraperResult]:
        # NumVerify requires API key, skip for now
        return None


class SocialMediaScanner(BaseScraper):
    """OSINT: Search social media platforms directly"""
    
    def __init__(self):
        super().__init__("social_media")
    
    async def scrape(self, phone: str) -> Optional[ScraperResult]:
        phone_clean = phone.lstrip('+')
        
        platforms = [
            ("telegram", f"https://t.me/{phone_clean}"),
            ("whatsapp", f"https://wa.me/{phone_clean}"),
            ("signal", f"https://signal.org/#/u/{phone_clean}"),
        ]
        
        try:
            async with aiohttp.ClientSession() as session:
                for platform, url in platforms:
                    result = await self._check_profile(session, platform, url)
                    if result:
                        return result
        except Exception as e:
            print(f"SocialMedia error: {e}")
        
        return None
    
    async def _check_profile(self, session, platform: str, url: str) -> Optional[ScraperResult]:
        try:
            async with session.head(url, timeout=5, allow_redirects=True) as response:
                if response.status == 200:
                    return ScraperResult(
                        name=f"Found on {platform.title()}",
                        confidence=0.3,
                        source=self.name,
                        raw_data={"platform": platform, "url": str(response.url)}
                    )
        except:
            pass
        return None


class UsernameCorrelationScraper(BaseScraper):
    """OSINT: Sherlock-style username enumeration from phone metadata"""
    
    def __init__(self):
        super().__init__("username_enum")
    
    async def scrape(self, phone: str) -> Optional[ScraperResult]:
        phone_clean = phone.lstrip('+')
        
        # Extract potential usernames from phone patterns
        potential_usernames = [
            phone_clean[-8:],
            phone_clean[-10:],
            phone_clean.replace('+', ''),
        ]
        
        try:
            async with aiohttp.ClientSession() as session:
                for username in potential_usernames[:2]:
                    result = await self._check_username(session, username)
                    if result:
                        return result
        except Exception as e:
            print(f"Username correlation error: {e}")
        
        return None
    
    async def _check_username(self, session, username: str) -> Optional[ScraperResult]:
        try:
            # Check common platforms for username
            sites = [
                ("github", f"https://github.com/{username}"),
                ("twitter", f"https://twitter.com/{username}"),
                ("instagram", f"https://instagram.com/{username}"),
            ]
            
            for platform, url in sites:
                try:
                    async with session.head(url, timeout=3) as response:
                        if response.status == 200:
                            return ScraperResult(
                                name=f"Username '{username}' found on {platform}",
                                confidence=0.4,
                                source=self.name,
                                raw_data={"username": username, "platform": platform}
                            )
                except:
                    continue
        except:
            pass
        return None


class WHOISDomainSearch(BaseScraper):
    """OSINT: Search WHOIS databases for phone in domain registrations"""
    
    def __init__(self):
        super().__init__("whois_search")
    
    async def scrape(self, phone: str) -> Optional[ScraperResult]:
        phone_clean = phone.lstrip('+')
        
        dorks = [
            f'"{phone}" "whois"',
            f'"{phone_clean}" "Registrar"',
            f'"{phone}" "domain registration"',
        ]
        
        try:
            async with aiohttp.ClientSession() as session:
                for dork in dorks[:2]:
                    result = await self._search_dork(session, dork)
                    if result:
                        return result
        except Exception as e:
            print(f"WHOIS search error: {e}")
        
        return None
    
    async def _search_dork(self, session, query: str) -> Optional[ScraperResult]:
        try:
            url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    html = await response.text()
                    if 'No results' not in html:
                        return ScraperResult(
                            name="Phone found in domain records",
                            confidence=0.3,
                            source=self.name,
                            raw_data={"query": query}
                        )
        except:
            pass
        return None


class BreachSearchScraper(BaseScraper):
    """OSINT: Search for phone in leaked databases"""
    
    def __init__(self):
        super().__init__("breach_search")
    
    async def scrape(self, phone: str) -> Optional[ScraperResult]:
        phone_clean = phone.lstrip('+')
        
        # Search for phone in breach dumps
        dorks = [
            f'"{phone}" "breach"',
            f'"{phone}" "leaked"',
            f'"{phone_clean}" "database"',
            f'"{phone}" "combolist"',
        ]
        
        try:
            async with aiohttp.ClientSession() as session:
                for dork in dorks[:2]:
                    result = await self._search_dork(session, dork)
                    if result:
                        return result
        except Exception as e:
            print(f"Breach search error: {e}")
        
        return None
    
    async def _search_dork(self, session, query: str) -> Optional[ScraperResult]:
        try:
            url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    html = await response.text()
                    if 'No results' not in html:
                        return ScraperResult(
                            name="Phone found in data breach",
                            confidence=0.4,
                            source=self.name,
                            raw_data={"query": query}
                        )
        except:
            pass
        return None


class PhoneInfogaScraper(BaseScraper):
    """OSINT: PhoneInfoga-style comprehensive scan"""
    
    def __init__(self):
        super().__init__("phoneinfoga")
    
    async def scrape(self, phone: str) -> Optional[ScraperResult]:
        phone_clean = phone.lstrip('+')
        
        results = []
        
        try:
            async with aiohttp.ClientSession(
                headers={"User-Agent": "PhoneInfoga/2.0"}
            ) as session:
                # Step 1: Local carrier lookup via phonenumbers
                carrier_result = await self._local_carrier_lookup(phone_clean)
                if carrier_result:
                    results.append(carrier_result)
                
                # Step 2: International number format
                format_result = await self._check_formats(session, phone_clean)
                if format_result:
                    results.append(format_result)
                
                # Step 3: Timezone from phone number
                timezone_result = await self._get_timezone(phone_clean)
                if timezone_result:
                    results.append(timezone_result)
                
                if results:
                    # Return first useful result
                    return results[0]
                    
        except Exception as e:
            print(f"PhoneInfoga error: {e}")
        
        return None
    
    async def _local_carrier_lookup(self, phone: str) -> Optional[ScraperResult]:
        try:
            import phonenumbers
            from phonenumbers import carrier, geocoder
            
            parsed = phonenumbers.parse(f"+{phone}")
            
            carrier_name = carrier.name_for_number(parsed, "en")
            region = geocoder.description_for_number(parsed, "en")
            
            info = []
            if carrier_name:
                info.append(f"Carrier: {carrier_name}")
            if region:
                info.append(f"Location: {region}")
            
            if info:
                return ScraperResult(
                    name=", ".join(info),
                    confidence=0.8,
                    source=self.name,
                    raw_data={
                        "carrier": carrier_name,
                        "region": region,
                        "phone": phone
                    }
                )
        except Exception as e:
            print(f"Local carrier lookup error: {e}")
        return None
    
    async def _check_formats(self, session, phone: str) -> Optional[ScraperResult]:
        try:
            import phonenumbers
            from phonenumbers import PhoneNumberFormat
            
            parsed = phonenumbers.parse(f"+{phone}")
            
            formats = {
                "E164": phonenumbers.format_number(parsed, PhoneNumberFormat.E164),
                "INTERNATIONAL": phonenumbers.format_number(parsed, PhoneNumberFormat.INTERNATIONAL),
                "NATIONAL": phonenumbers.format_number(parsed, PhoneNumberFormat.NATIONAL),
            }
            
            return ScraperResult(
                name=f"Valid: {phonenumbers.is_valid_number(parsed)}",
                confidence=0.9,
                source=self.name,
                raw_data={"formats": formats, "phone": phone}
            )
        except:
            pass
        return None
    
    async def _get_timezone(self, phone: str) -> Optional[ScraperResult]:
        try:
            import phonenumbers
            from phonenumbers import timezone
            
            parsed = phonenumbers.parse(f"+{phone}")
            timezones = timezone.time_zones_for_number(parsed)
            
            if timezones:
                return ScraperResult(
                    name=f"Timezone: {timezones[0]}",
                    confidence=0.8,
                    source=self.name,
                    raw_data={"timezones": list(timezones), "phone": phone}
                )
        except:
            pass
        return None


class PublicRecordsScraper(BaseScraper):
    """OSINT: Search people search engines and public records"""
    
    def __init__(self):
        super().__init__("public_records")
    
    async def scrape(self, phone: str) -> Optional[ScraperResult]:
        phone_clean = phone.lstrip('+')
        
        dorks = [
            f'"{phone}" "people search"',
            f'"{phone}" "reverse phone"',
            f'"{phone}" "phone number lookup"',
            f'"{phone}" "who is this"',
        ]
        
        try:
            async with aiohttp.ClientSession() as session:
                for dork in dorks[:2]:
                    result = await self._search_dork(session, dork)
                    if result:
                        return result
        except Exception as e:
            print(f"Public records error: {e}")
        
        return None
    
    async def _search_dork(self, session, query: str) -> Optional[ScraperResult]:
        try:
            url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    html = await response.text()
                    if 'No results' not in html:
                        return ScraperResult(
                            name="Found in people search results",
                            confidence=0.3,
                            source=self.name,
                            raw_data={"query": query}
                        )
        except:
            pass
        return None


class PhoneMetadataScraper(BaseScraper):
    """OSINT: Get phone metadata from various sources"""
    
    def __init__(self):
        super().__init__("phone_metadata")
    
    async def scrape(self, phone: str) -> Optional[ScraperResult]:
        phone_clean = phone.lstrip('+')
        
        dorks = [
            f'"{phone}" site:docs.google.com',
            f'"{phone}" site:sheets.google.com',
            f'"{phone}" filetype:pdf',
        ]
        
        try:
            async with aiohttp.ClientSession() as session:
                for dork in dorks[:2]:
                    result = await self._search_dork(session, dork)
                    if result:
                        return result
        except Exception as e:
            print(f"Phone metadata error: {e}")
        
        return None
    
    async def _search_dork(self, session, query: str) -> Optional[ScraperResult]:
        try:
            url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    html = await response.text()
                    if 'No results' not in html:
                        return ScraperResult(
                            name="Phone found in public document",
                            confidence=0.4,
                            source=self.name,
                            raw_data={"query": query}
                        )
        except:
            pass
        return None
