import asyncio
from concurrent.futures import ThreadPoolExecutor

class ExecutorManager:
    _instance = None
    _executor = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_executor(self):
        if self._executor is None:
            import os
            max_workers = min(8, (os.cpu_count() or 1) + 4)
            self._executor = ThreadPoolExecutor(max_workers=max_workers)
        return self._executor
    
    async def run_in_executor(self, func, *args):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.get_executor(), func, *args)

executor_manager = ExecutorManager()
