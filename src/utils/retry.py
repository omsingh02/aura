import asyncio
import functools

def async_retry(max_attempts=3, base_delay=1.0, exponential_base=2.0):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts:
                        raise
                    delay = base_delay * (exponential_base ** (attempt - 1))
                    await asyncio.sleep(delay)
        return wrapper
    return decorator
