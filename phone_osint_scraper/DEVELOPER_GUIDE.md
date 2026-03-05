# Developer Guide - Phone OSINT Scraper

## Prerequisites

- Python 3.11+
- ClickHouse (running locally or via Docker)
- Redis (optional, for caching)

## Setup

### 1. Create Virtual Environment

```bash
cd phone_osint_scraper

# Create venv (if not exists)
python3 -m venv venv

# Activate venv
source venv/bin/activate

# Install dependencies
pip install -e .
pip install pandas  # if not auto-installed
```

### 2. Start ClickHouse (Local)

```bash
# Using Docker
cd docker
docker compose up -d clickhouse

# Or install ClickHouse directly:
# https://clickhouse.com/docs/en/install
```

Wait for ClickHouse to be healthy:
```bash
docker ps  # Check status is "healthy"
```

### 3. Configure Environment

Edit `.env` file:
```bash
CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=8123
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=osint_password
CLICKHOUSE_DB=default
REDIS_HOST=localhost
REDIS_PORT=6379

# API Keys (get free keys below)
TRUECALLER_API_KEY=
NUMVERIFY_API_KEY=
```

### 4. Initialize Database

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
print('Table created!')
ch.close()
"
```

## Running Tests

### Test Utils (No API needed)
```bash
source venv/bin/activate
python -c "
from src.core.utils import PhoneNormalizer, CountryDetector
print('Normalize +923001234567:', PhoneNormalizer.normalize('+923001234567'))
print('Detect +923001234567:', CountryDetector.detect('+923001234567'))
"
```

### Test ClickHouse Connection
```bash
source venv/bin/activate
python -c "
from src.core.clickhouse import ClickHouseClient
ch = ClickHouseClient()
result = ch.client.query('SELECT 1')
print('ClickHouse:', result.result_rows)
ch.close()
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
    orch = NameFirstOrchestrator(ch)
    status = await orch.process_phone('+923001234567')
    print(f'Status: {status}')
    result = ch.query_recent('+923001234567')
    print(result[['phone', 'owner_name', 'country', 'status']])
    ch.close()

asyncio.run(test())
"
```

### Using CLI
```bash
# Single phone
source venv/bin/activate
python cli.py --phone "+923001234567"

# Batch mode
python cli.py --batch phones.txt
```

## Getting Free API Keys

### Numverify (Free tier: 100 requests/month)
1. Go to https://numverify.com/documentation
2. Sign up for free API access
3. Add key to `.env`: `NUMVERIFY_API_KEY=your_key`

### Truecaller (Requires app installation)
1. Install Truecaller app on Android
2. Use their web API (requires authentication)
3. Add key to `.env`: `TRUECALLER_API_KEY=your_key`

## Project Structure

```
phone_osint_scraper/
├── src/
│   ├── core/
│   │   ├── config.py        # Settings
│   │   ├── orchestrator.py  # Main pipeline
│   │   ├── clickhouse.py    # DB client
│   │   └── utils.py         # Phone normalization
│   ├── pipelines/
│   │   ├── name_finder.py   # Find owner name
│   │   ├── id_enricher.py   # CNIC/SECP/FBR
│   │   └── address_enricher.py
│   ├── scrapers/
│   │   ├── name_scrapers.py # Truecaller, Numverify, Whitepages
│   │   └── pakistan.py      # PakWheels, Jang
│   └── models/
│       ├── clickhouse_row.py
│       └── phone_input.py
├── cli.py                   # CLI interface
├── batch_processor.py       # Batch processing
├── .env                     # Environment config
└── pyproject.toml
```

## Expected Behavior

- **With API keys**: Fetches real data from providers
- **Without API keys**: Returns "failed" status (no name found)
- **All lookups**: Stored in ClickHouse for analytics
