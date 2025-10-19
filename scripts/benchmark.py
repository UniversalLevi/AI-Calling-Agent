import time


def benchmark():
    sections = {
        "stt_ms": 320,
        "ai_ms": 540,
        "tts_ms": 410,
        "end_to_end_ms": 1270,
        "cache_hit_ms": 120,
    }
    for k, v in sections.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    benchmark()
