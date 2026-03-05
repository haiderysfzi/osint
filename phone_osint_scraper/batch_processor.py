import asyncio
import sys
from typing import List
from src.core.orchestrator import NameFirstOrchestrator
from src.core.clickhouse import ClickHouseClient

class BatchProcessor:
    def __init__(self, concurrency: int = 10):
        self.concurrency = concurrency
        self.clickhouse = ClickHouseClient()
        self.orchestrator = NameFirstOrchestrator(self.clickhouse)

    async def _worker(self, queue: asyncio.Queue):
        while True:
            phone = await queue.get()
            try:
                status = await self.orchestrator.process_phone(phone)
                print(f"Processed: {phone} - {status}")
            except Exception as e:
                print(f"Error processing {phone}: {e}")
            finally:
                queue.task_done()

    async def process_file(self, file_path: str):
        queue = asyncio.Queue()
        
        # Load phones into queue
        with open(file_path, 'r') as f:
            for line in f:
                phone = line.strip()
                if phone:
                    await queue.put(phone)
        
        # Start workers
        workers = [asyncio.create_task(self._worker(queue)) for _ in range(self.concurrency)]
        
        # Wait for all phones to be processed
        await queue.join()
        
        # Cancel workers
        for worker in workers:
            worker.cancel()
        
        await asyncio.gather(*workers, return_exceptions=True)
        self.clickhouse.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python batch_processor.py <phone_file>")
        sys.exit(1)
        
    processor = BatchProcessor(concurrency=10)
    asyncio.run(processor.process_file(sys.argv[1]))
