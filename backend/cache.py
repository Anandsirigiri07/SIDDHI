# backend/cache.py
import time
import hashlib
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("siddhi.cache")

class SimpleTTLCache:
    def __init__(self, default_ttl_seconds: int = 900): # 15 minutes default
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl_seconds

    def _generate_key(self, prefix: str, data: Any) -> str:
        serialized = json.dumps(data, sort_keys=True, default=str)
        hash_str = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        return f"{prefix}:{hash_str}"

    def get(self, prefix: str, key_data: Any) -> Optional[Any]:
        key = self._generate_key(prefix, key_data)
        item = self._cache.get(key)
        if not item:
            return None
        if time.time() > item["expires_at"]:
            del self._cache[key]
            return None
        logger.info(f"Cache HIT for key prefix '{prefix}'")
        return item["value"]

    def set(self, prefix: str, key_data: Any, value: Any, ttl_seconds: Optional[int] = None):
        key = self._generate_key(prefix, key_data)
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        self._cache[key] = {
            "value": value,
            "expires_at": time.time() + ttl
        }

    def clear(self):
        self._cache.clear()

# Global in-memory cache instance
siddhi_cache = SimpleTTLCache()
