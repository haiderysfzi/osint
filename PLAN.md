# Phone OSINT Scraper - ClickHouse Pipeline

## Requirements
**Input**: Mobile number (e.g., `+923001234567`)  
**Output**: Owner Name, Address, CNIC/ID, Company  
**Storage**: ClickHouse  
**Philosophy**: No third-party APIs. Use real OSINT methods hackers use.

## Project Structure
```
phone_osint_scraper/
├── src/
│   ├── core/
│   │   ├── config.py
│   │   ├── orchestrator.py      # Main pipeline
│   │   └── clickhouse.py        # DB ingestion
│   ├── pipelines/
│   │   ├── name_finder.py       # Owner name extraction
│   │   ├── id_enricher.py       # CNIC/SECP/FBR
│   │   └── address_enricher.py
│   ├── scrapers/
│   │   ├── osint_scrapers.py    # OSINT methods (NO API keys)
│   │   ├── name_scrapers.py     # Legacy (to remove)
│   │   └── pakistan.py          # Local sources
│   └── models/
│       └── clickhouse_row.py
├── cli.py
├── batch_processor.py
└── .env
```

## OSINT Methods (No Third-Party APIs)

### 1. Google Dorking
- Search phone numbers in Google results
- Query patterns: `"+923001234567"`, `site:facebook.com "+923001234567"`
- Source: DuckDuckGo HTML (no API needed)

### 2. Social Media Scanner
- Check Telegram, WhatsApp, Signal profile existence
- Direct platform URL checks

### 3. Data Breach Search
- Search public breach collections
- Note: Requires access to breach databases

### 4. Public Documents
- Search Google Docs/Sheets for phone
- Dork: `site:docs.google.com "phone"`

### 5. WHOIS Domain Search
- Find phone in domain registration records

### 6. Local Pakistan Sources
- SECP (Securities and Exchange Commission)
- FBR (Federal Board of Revenue)
- PakWheels, Jang classifieds

## ClickHouse Schema
```sql
CREATE TABLE phone_osint_results (
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
ORDER BY (phone, ingested_at);
```

## Pipeline Flow
```
Input: +923001234567
│
├── 1. Google Dork Search (DuckDuckGo)
│   ├── Search phone in Google results
│   ├── Search social media mentions
│   └── Search public documents
│
├── 2. Social Media Check
│   ├── Telegram profile
│   ├── WhatsApp business
│   └── Signal
│
├── 3. If PK number → Local Enrichment
│   ├── SECP company lookup
│   ├── FBR taxpayer search
│   └── Classifieds (PakWheels, Jang)
│
├── 4. Store in ClickHouse
│   └── All attempts logged
│
└── Return result
```

## Running

### Prerequisites
- Python 3.11+
- ClickHouse (Docker or local)

### Setup
```bash
cd phone_osint_scraper
source venv/bin/activate
pip install -e .
pip install beautifulsoup4 lxml aiohttp

# Start ClickHouse
docker compose -f docker/docker-compose.yml up -d clickhouse
```

### Test
```bash
python -c "
import asyncio
from src.core.orchestrator import NameFirstOrchestrator
from src.core.clickhouse import ClickHouseClient

async def test():
    ch = ClickHouseClient()
    orch = NameFirstOrchestrator(ch)
    status = await orch.process_phone('+923001234567')
    print(f'Status: {status}')
    ch.close()

asyncio.run(test())
"

# Or via CLI
python cli.py --phone "+923001234567"
python cli.py --batch phones.txt
```

## Dependencies
- clickhouse-connect
- pydantic
- phonenumbers
- aiohttp
- beautifulsoup4
- lxml
- python-dotenv
- click
- pandas
- redis

## Philosophy
- NO third-party paid APIs
- NO API keys required
- Use OSINT techniques hackers use
- All lookups stored for analytics
- Graceful degradation (no data = failed status)
