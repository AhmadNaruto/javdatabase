from asyncio import ensure_future

import lru


def session_purged(key, value):
    print(f"[session purge] host : {key} session has closed and remove")
    ensure_future(value.close())


sessions_cache = lru.LRU(size=10, callback=session_purged)

header = "Mozilla/5.0 (Linux; Android 7.0; 5060 Build/NRD90M; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/58.0.3029.83 Mobile Safari/537.36"
