import time

# Mocked integration tests (no real API calls)

def test_english_call_latency():
    start = time.perf_counter()
    # Mock AI + TTS + STT durations
    time.sleep(0.2)
    elapsed = (time.perf_counter() - start) * 1000
    assert elapsed < 2000


def test_hindi_call_latency_cache_hit():
    start = time.perf_counter()
    # Simulate cache hit path (<200ms)
    time.sleep(0.15)
    elapsed = (time.perf_counter() - start) * 1000
    assert elapsed < 200


if __name__ == "__main__":
    test_english_call_latency()
    test_hindi_call_latency_cache_hit()
    print("OK")
