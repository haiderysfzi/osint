import click
import asyncio
import sys
from src.core.orchestrator import NameFirstOrchestrator
from src.core.clickhouse import ClickHouseClient

async def run_single(phone: str):
    clickhouse = ClickHouseClient()
    orchestrator = NameFirstOrchestrator(clickhouse)
    try:
        status = await orchestrator.process_phone(phone)
        print(f"Phone: {phone} - Status: {status}")
    finally:
        clickhouse.close()

async def run_batch(file):
    clickhouse = ClickHouseClient()
    orchestrator = NameFirstOrchestrator(clickhouse)
    try:
        for line in file:
            phone = line.strip()
            if phone:
                status = await orchestrator.process_phone(phone)
                print(f"Phone: {phone} - Status: {status}")
    finally:
        clickhouse.close()

@click.command()
@click.option('--phone', help='Single phone number to lookup (e.g., +923001234567)')
@click.option('--batch', type=click.File('r'), help='File containing phone numbers, one per line')
def process(phone: str, batch):
    """Production Phone OSINT Scraper CLI."""
    if not phone and not batch:
        print("Error: Either --phone or --batch must be provided.")
        sys.exit(1)
    
    if phone:
        asyncio.run(run_single(phone))
    elif batch:
        asyncio.run(run_batch(batch))

if __name__ == '__main__':
    process()
