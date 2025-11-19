import asyncio
from concurrent.futures import ThreadPoolExecutor


class ExecutorManager:
    _instance = None
    _executor = None
    _loop = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_executor(self):
        if self._executor is None:
            import os
            max_workers = min(8, (os.cpu_count() or 1) + 4)
            self._executor = ThreadPoolExecutor(
                max_workers=max_workers,
                thread_name_prefix="shazam_io"
            )
        
        return self._executor
    
    def get_loop(self):
        if self._loop is None or self._loop.is_closed():
            self._loop = asyncio.get_event_loop()
        return self._loop
    
    async def run_in_executor(self, func, *args):
        loop = self.get_loop()
        executor = self.get_executor()
        return await loop.run_in_executor(executor, func, *args)
    
    def shutdown(self, wait=True):
        if self._executor:
            self._executor.shutdown(wait=wait)
            self._executor = None
        self._loop = None
executor_manager = ExecutorManager()
