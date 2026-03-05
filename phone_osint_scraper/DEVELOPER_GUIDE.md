# Developer Guide - Phone OSINT Scraper

## Philosophy
**No third-party APIs** - Uses real OSINT methods hackers use:
- Google Dorking (DuckDuckGo HTML)
- Social Media checks (Telegram, WhatsApp, Signal)
- Public document search
- WHOIS domain records
- Local Pakistan sources (SECP, FBR, classifieds)

## Prerequisites

- Python 3.11+
- ClickHouse (running locally or via Docker)
- Redis (optional)

## Setup

### 1. Create Virtual Environment

```bash
cd phone_osint_scraper
python3 -m venv venv
source venv/bin/activate
pip install -e .
pip install pandas beautifulsoup4 lxml
```

### 2. Start ClickHouse

```bash
cd docker
docker compose up -d clickhouse
```

### 3. Initialize Database

```bash
python -c "
from src.core.clickhouse import ClickHouseClient
ch = ClickHouseClient()
ch.client.command('''
CREATE TABLE IF NOT EXISTS phone_osint_results (
    ingested_at DateTime64(3) DEFAULT now64(3),
    phone String,
    owner_name String,
    owner_name_confidence Float64,
    cnic Nullable(String),
    passport Nullable(String),
    address Nullable(String),
    country String,
    companies Array(String),
    sources Array(String),
    raw_json String,
    pipeline_duration UInt32,
    status Enum8('success' = 1, 'partial' = 2, 'failed' = 3)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(ingested_at)
ORDER BY (phone, ingested_at)
''')
ch.close()
print('Done!')
"
```

## Running Tests

### Test Utils
```bash
source venv/bin/activate
python -c "
from src.core.utils import PhoneNormalizer, CountryDetector
print(PhoneNormalizer.normalize('+923001234567'))
print(CountryDetector.detect('+923001234567'))
"
```

### Test Full Pipeline
```bash
source venv/bin/activate
python -c "
import asyncio
from src.core.orchestrator import NameFirstOrchestrator
from src.core.clickhouse import ClickHouseClient

async def test():
    ch = ClickHouseClient()
    ch.client.command('TRUNCATE TABLE phone_osint_results')
    orch = NameFirstOrchestrator(ch)
    
    status = await orch.process_phone('+923001234567')
    print(f'Status: {status}')
    
    result = ch.client.query_df('SELECT phone, owner_name, country, status FROM phone_osint_results')
    print(result)
    ch.close()

asyncio.run(test())
"
```

### Using CLI
```bash
python cli.py --phone "+923001234567"
python cli.py --batch phones.txt
```

## OSINT Methods Used

1. **GoogleDorkScraper** - Searches DuckDuckGo for phone mentions
2. **SocialMediaScanner** - Checks Telegram/WhatsApp/Signal profiles
3. **PhoneNumberInfoScraper** - Searches public Google Docs/Sheets
4. **WHOISScraper** - Checks domain registration records
5. **PakWheelsScraper** / **JangScraper** - Pakistan classifieds

## Project Structure

```
phone_osint_scraper/
├── src/
│   ├── core/
│   │   ├── config.py
│   │   ├── orchestrator.py
│   │   ├── clickhouse.py
│   │   └── utils.py
│   ├── pipelines/
│   │   ├── name_finder.py
│   │   ├── id_enricher.py
│   │   └── address_enricher.py
│   ├── scrapers/
│   │   ├── osint_scrapers.py    # Main scrapers
│   │   ├── name_scrapers.py     # Legacy
│   │   └── pakistan.py
│   └── models/
├── cli.py
├── .env
└── pyproject.toml
```
