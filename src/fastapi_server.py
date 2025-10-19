import os
import time
import asyncio
from typing import Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from .debug_logger import logger, debug_enabled
except Exception:
    class _Null:
        def __getattr__(self, *_):
            return lambda *a, **k: None
    logger = _Null()
    def debug_enabled():
        return False


app = FastAPI(title="Sara FastAPI Server", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_start_time = time.time()


@app.get("/health")
async def health() -> Dict:
    return {
        "status": "OK",
        "uptime": round(time.time() - _start_time, 2),
        "debug": debug_enabled(),
    }


async def _warm_tts_cache_async():
    try:
        from .tts_cache import initialize_tts_cache
        from .enhanced_hindi_tts import EnhancedHindiTTS

        tts = EnhancedHindiTTS()

        def tts_func(text: str) -> str:
            # Returns generated file path (mp3)
            return tts.speak_openai(text) or ""

        initialize_tts_cache(tts_func)
        logger.info("TTS cache warmup completed")
    except Exception as e:
        logger.error(f"TTS cache warmup failed: {e}")


async def _start_health_monitor():
    try:
        from .health_monitor import start_health_monitor
        await start_health_monitor()
    except Exception as e:
        logger.error(f"Health monitor start failed: {e}")


@app.on_event("startup")
async def on_startup():
    if debug_enabled():
        asyncio.create_task(_warm_tts_cache_async())
        asyncio.create_task(_start_health_monitor())


def run(host: str = "0.0.0.0", port: int = 8001):
    import uvicorn
    uvicorn.run(app, host=host, port=port, log_level="info")


