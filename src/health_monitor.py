import os
import asyncio
import time
from typing import Dict

try:
    import psutil
except Exception:
    psutil = None

try:
    from .debug_logger import logger, debug_enabled
except Exception:
    class _Null:
        def __getattr__(self, *_):
            return lambda *a, **k: None
    logger = _Null()
    def debug_enabled():
        return False


def _snapshot() -> Dict:
    mem_info = psutil.Process(os.getpid()).memory_info() if psutil else None
    return {
        "rss_mb": round((mem_info.rss / (1024 * 1024)) if mem_info else 0, 2),
        "vms_mb": round((mem_info.vms / (1024 * 1024)) if mem_info else 0, 2),
        "tasks": len(asyncio.all_tasks()) if hasattr(asyncio, "all_tasks") else 0,
        "time": time.strftime("%H:%M:%S"),
    }


async def report_to_dashboard(stats: Dict):
    try:
        # Placeholder endpoint for future use
        # Could POST to dashboard if desired
        pass
    except Exception as e:
        logger.error(f"Health monitor report failed: {e}")


async def start_health_monitor(interval_sec: int = 30):
    if not debug_enabled():
        return
    while True:
        try:
            stats = _snapshot()
            logger.debug(f"[HEALTH] rss={stats['rss_mb']}MB vms={stats['vms_mb']}MB tasks={stats['tasks']}")
            await report_to_dashboard(stats)
        except Exception as e:
            logger.error(f"Health monitor error: {e}")
        await asyncio.sleep(interval_sec)


