import asyncio
import functools
from typing import TypeVar, Callable, Any, Type
from ..utils.logger import log


T = TypeVar('T')


def async_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential_base: float = 2.0,
    exceptions: tuple[Type[Exception], ...] = (Exception,)
):
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts:
                        log(f"❌ {func.__name__} failed after {max_attempts} attempts: {e}", "ERROR")
                        raise
                    delay = min(base_delay * (exponential_base ** (attempt - 1)), max_delay)
                    
                    log(f"⚠️ {func.__name__} attempt {attempt}/{max_attempts} failed: {type(e).__name__}. Retrying in {delay:.1f}s...", "WARNING")
                    await asyncio.sleep(delay)
            if last_exception:
                raise last_exception
        
        return wrapper
    return decorator
