# TASKS.md

## Sprint 1: Project Setup & Infrastructure

### Task 1: Create Project Directory Structure
- [x] Create `phone_osint_scraper/` root directory
- [x] Create `src/core/`, `src/pipelines/`, `src/scrapers/`, `src/models/`
- [x] Create `clickhouse/`, `clickhouse/migrations/`
- [x] Create `docker/`
- [x] Initialize `pyproject.toml` with dependencies

### Task 2: Create ClickHouse Schema
- [x] Create `clickhouse/schema.sql` with table DDL
- [x] Add materialized views for analytics
- [x] Test schema on local ClickHouse instance

### Task 3: Create Docker Compose
- [x] Create `docker/docker-compose.yml`
- [x] Add ClickHouse service
- [x] Add Redis service
- [x] Add scraper service configuration


## Sprint 2: Core Models & Infrastructure

### Task 4: Implement Pydantic Models
- [x] Create `src/models/phone_input.py` - Single mobile number input model
- [x] Create `src/models/clickhouse_row.py` - DB schema model with all fields
- [x] Add validation for E.164 phone format
- [x] Add `to_pandas()` conversion method

### Task 5: Implement ClickHouse Client
- [x] Create `src/core/clickhouse.py`
- [x] Implement `insert()` method for single/batch rows
- [x] Implement `query_recent()` for fetching results
- [x] Add connection pooling and error handling

### Task 6: Implement Config & Utilities
- [x] Create `src/core/config.py` - Environment config management
- [x] Implement phone normalizer (E.164 format)
- [x] Implement country detector from phone number


## Sprint 3: OSINT Scrapers (No Third-Party APIs)

### Task 7: Google Dork Scraper
- [x] Create `src/scrapers/osint_scrapers.py`
- [x] Implement DuckDuckGo search (no API key)
- [x] Add phone number search patterns
- [x] Extract name from search results

### Task 8: Social Media Scanner
- [x] Implement Telegram profile check
- [x] Implement WhatsApp business check
- [x] Implement Signal profile check

### Task 9: Public Data Scrapers
- [x] Implement Google Docs/Sheets search
- [x] Implement WHOIS domain search
- [x] Add Pakistan local sources (PakWheels, Jang)


## Sprint 4: Pipelines (Enrichment)

### Task 10: Implement Name Finder Pipeline
- [x] Create `src/pipelines/name_finder.py`
- [x] Run scrapers in parallel
- [x] Select best name result by confidence
- [x] Handle no-name found case

### Task 11: Implement ID Enricher (CNIC/SECP/FBR)
- [x] Create `src/pipelines/id_enricher.py`
- [x] Implement SECP company lookup
- [x] Implement FBR taxpayer lookup
- [x] Implement CNIC extraction logic

### Task 12: Implement Address Enricher
- [x] Create `src/pipelines/address_enricher.py`
- [x] Implement Google Maps validation (optional)
- [x] Add address parsing and normalization


## Sprint 5: Orchestrator & CLI

### Task 13: Implement NameFirstOrchestrator
- [x] Create `src/core/orchestrator.py`
- [x] Implement step 1: Find name (parallel)
- [x] Implement step 2: Enrich with ID/address
- [x] Implement step 3: Store in ClickHouse
- [x] Add timing and error handling

### Task 14: Implement CLI
- [x] Create `cli.py` with Click commands
- [x] Add `--phone` option for single lookup
- [x] Add `--batch` option for file input
- [x] Add output formatting

### Task 15: Implement Batch Processor
- [x] Create `batch_processor.py`
- [x] Implement concurrent phone processing
- [x] Add progress tracking
- [x] Add retry logic for failed lookups


## Sprint 6: Testing & Polish

### Task 16: Create Tests
- [ ] Write unit tests for models
- [ ] Write unit tests for orchestrator
- [ ] Write integration tests for scrapers
- [ ] Add mock responses for testing

### Task 17: End-to-End Testing
- [x] Start ClickHouse locally
- [x] Test full pipeline with sample numbers
- [x] Verify data in ClickHouse
- [x] Test batch processing

### Task 18: Error Handling & Logging
- [x] Add comprehensive logging
- [x] Handle scraper failures gracefully
- [ ] Add alerting for failed pipelines
- [ ] Document error scenarios
