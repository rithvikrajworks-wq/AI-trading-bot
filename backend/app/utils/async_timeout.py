# backend/app/utils/async_timeout.py

"""Utility for applying explicit async timeouts to coroutines.
Usage: await with_timeout(coro, timeout_seconds)
"""

import asyncio
from typing import Any

async def with_timeout(coro: Any, timeout: float) -> Any:
    """Run *coro* with a timeout.

    Raises ``asyncio.TimeoutError`` if the operation exceeds *timeout* seconds.
    """
    return await asyncio.wait_for(coro, timeout)
