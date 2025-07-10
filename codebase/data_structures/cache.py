from typing import Any, Optional, Dict, List
from collections import OrderedDict
import time
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class EvictionPolicy(Enum):
    LRU = "least_recently_used"
    LFU = "least_frequently_used"
    FIFO = "first_in_first_out"
    LIFO = "last_in_first_out"
    TTL = "time_to_live"


@dataclass
class CacheItem:
    """Represents an item in the cache"""
    key: Any
    value: Any
    access_count: int = 0
    created_time: float = 0.0
    last_accessed: float = 0.0
    ttl: Optional[float] = None  # Time to live in seconds
    
    def __post_init__(self):
        current_time = time.time()
        if self.created_time == 0.0:
            self.created_time = current_time
        if self.last_accessed == 0.0:
            self.last_accessed = current_time
    
    def is_expired(self) -> bool:
        """Check if item has expired based on TTL"""
        if self.ttl is None:
            return False
        return time.time() - self.created_time > self.ttl
    
    def touch(self) -> None:
        """Update access information"""
        self.access_count += 1
        self.last_accessed = time.time()


class Cache(ABC):
    """Abstract base class for cache implementations"""
    
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.size = 0
        self._lock = threading.RLock()
    
    @abstractmethod
    def get(self, key: Any) -> Optional[Any]:
        """Get value by key"""
        pass
    
    @abstractmethod
    def put(self, key: Any, value: Any, ttl: Optional[float] = None) -> None:
        """Put key-value pair in cache"""
        pass
    
    @abstractmethod
    def delete(self, key: Any) -> bool:
        """Delete key from cache"""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all items from cache"""
        pass
    
    @abstractmethod
    def keys(self) -> List[Any]:
        """Get all keys in cache"""
        pass
    
    def __len__(self) -> int:
        return self.size
    
    def __contains__(self, key: Any) -> bool:
        return self.get(key) is not None


class LRUCache(Cache):
    """Least Recently Used Cache implementation"""
    
    def __init__(self, capacity: int):
        super().__init__(capacity)
        self._cache: OrderedDict[Any, CacheItem] = OrderedDict()
    
    def get(self, key: Any) -> Optional[Any]:
        """Get value and mark as recently used"""
        with self._lock:
            if key not in self._cache:
                return None
            
            item = self._cache[key]
            
            # Check if expired
            if item.is_expired():
                del self._cache[key]
                self.size -= 1
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            item.touch()
            
            return item.value
    
    def put(self, key: Any, value: Any, ttl: Optional[float] = None) -> None:
        """Put key-value pair, evicting LRU item if necessary"""
        with self._lock:
            # If key exists, update it
            if key in self._cache:
                self._cache[key].value = value
                if ttl is not None:
                    self._cache[key].ttl = ttl
                self._cache.move_to_end(key)
                return
            
            # If at capacity, remove LRU item
            if self.size >= self.capacity:
                self._evict()
            
            # Add new item
            item = CacheItem(key, value, ttl=ttl)
            self._cache[key] = item
            self.size += 1
    
    def delete(self, key: Any) -> bool:
        """Delete key from cache"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self.size -= 1
                return True
            return False
    
    def clear(self) -> None:
        """Clear all items"""
        with self._lock:
            self._cache.clear()
            self.size = 0
    
    def keys(self) -> List[Any]:
        """Get all keys"""
        with self._lock:
            return list(self._cache.keys())
    
    def _evict(self) -> None:
        """Evict least recently used item"""
        if self._cache:
            self._cache.popitem(last=False)  # Remove first (oldest) item
            self.size -= 1
    
    def _cleanup_expired(self) -> None:
        """Remove expired items"""
        with self._lock:
            expired_keys = [key for key, item in self._cache.items() if item.is_expired()]
            for key in expired_keys:
                del self._cache[key]
                self.size -= 1


class LFUCache(Cache):
    """Least Frequently Used Cache implementation"""
    
    def __init__(self, capacity: int):
        super().__init__(capacity)
        self._cache: Dict[Any, CacheItem] = {}
        self._frequencies: Dict[int, OrderedDict] = {}
        self._min_frequency = 0
    
    def get(self, key: Any) -> Optional[Any]:
        """Get value and increment frequency"""
        with self._lock:
            if key not in self._cache:
                return None
            
            item = self._cache[key]
            
            # Check if expired
            if item.is_expired():
                self._remove_key(key)
                return None
            
            # Update frequency
            self._update_frequency(key, item)
            item.touch()
            
            return item.value
    
    def put(self, key: Any, value: Any, ttl: Optional[float] = None) -> None:
        """Put key-value pair, evicting LFU item if necessary"""
        with self._lock:
            if self.capacity <= 0:
                return
            
            # If key exists, update it
            if key in self._cache:
                self._cache[key].value = value
                if ttl is not None:
                    self._cache[key].ttl = ttl
                self._update_frequency(key, self._cache[key])
                return
            
            # If at capacity, remove LFU item
            if self.size >= self.capacity:
                self._evict()
            
            # Add new item with frequency 1
            item = CacheItem(key, value, access_count=1, ttl=ttl)
            self._cache[key] = item
            
            if 1 not in self._frequencies:
                self._frequencies[1] = OrderedDict()
            self._frequencies[1][key] = True
            self._min_frequency = 1
            self.size += 1
    
    def delete(self, key: Any) -> bool:
        """Delete key from cache"""
        with self._lock:
            if key in self._cache:
                self._remove_key(key)
                return True
            return False
    
    def clear(self) -> None:
        """Clear all items"""
        with self._lock:
            self._cache.clear()
            self._frequencies.clear()
            self._min_frequency = 0
            self.size = 0
    
    def keys(self) -> List[Any]:
        """Get all keys"""
        with self._lock:
            return list(self._cache.keys())
    
    def _update_frequency(self, key: Any, item: CacheItem) -> None:
        """Update frequency tracking for a key"""
        old_freq = item.access_count
        new_freq = old_freq + 1
        
        # Remove from old frequency list
        if old_freq in self._frequencies and key in self._frequencies[old_freq]:
            del self._frequencies[old_freq][key]
            
            # Update min frequency if necessary
            if self._min_frequency == old_freq and len(self._frequencies[old_freq]) == 0:
                self._min_frequency += 1
        
        # Add to new frequency list
        if new_freq not in self._frequencies:
            self._frequencies[new_freq] = OrderedDict()
        self._frequencies[new_freq][key] = True
        
        item.access_count = new_freq
    
    def _evict(self) -> None:
        """Evict least frequently used item"""
        if self._min_frequency in self._frequencies and self._frequencies[self._min_frequency]:
            key_to_remove = next(iter(self._frequencies[self._min_frequency]))
            self._remove_key(key_to_remove)
    
    def _remove_key(self, key: Any) -> None:
        """Remove key from cache and frequency tracking"""
        if key in self._cache:
            item = self._cache[key]
            freq = item.access_count
            
            del self._cache[key]
            if freq in self._frequencies and key in self._frequencies[freq]:
                del self._frequencies[freq][key]
            
            self.size -= 1


class FIFOCache(Cache):
    """First In First Out Cache implementation"""
    
    def __init__(self, capacity: int):
        super().__init__(capacity)
        self._cache: Dict[Any, CacheItem] = {}
        self._insertion_order: List[Any] = []
    
    def get(self, key: Any) -> Optional[Any]:
        """Get value without affecting order"""
        with self._lock:
            if key not in self._cache:
                return None
            
            item = self._cache[key]
            
            # Check if expired
            if item.is_expired():
                self._remove_key(key)
                return None
            
            item.touch()
            return item.value
    
    def put(self, key: Any, value: Any, ttl: Optional[float] = None) -> None:
        """Put key-value pair, evicting first inserted item if necessary"""
        with self._lock:
            # If key exists, update it
            if key in self._cache:
                self._cache[key].value = value
                if ttl is not None:
                    self._cache[key].ttl = ttl
                return
            
            # If at capacity, remove first item
            if self.size >= self.capacity:
                self._evict()
            
            # Add new item
            item = CacheItem(key, value, ttl=ttl)
            self._cache[key] = item
            self._insertion_order.append(key)
            self.size += 1
    
    def delete(self, key: Any) -> bool:
        """Delete key from cache"""
        with self._lock:
            if key in self._cache:
                self._remove_key(key)
                return True
            return False
    
    def clear(self) -> None:
        """Clear all items"""
        with self._lock:
            self._cache.clear()
            self._insertion_order.clear()
            self.size = 0
    
    def keys(self) -> List[Any]:
        """Get all keys"""
        with self._lock:
            return list(self._cache.keys())
    
    def _evict(self) -> None:
        """Evict first inserted item"""
        if self._insertion_order:
            first_key = self._insertion_order[0]
            self._remove_key(first_key)
    
    def _remove_key(self, key: Any) -> None:
        """Remove key from cache and insertion order"""
        if key in self._cache:
            del self._cache[key]
            if key in self._insertion_order:
                self._insertion_order.remove(key)
            self.size -= 1


class TTLCache(Cache):
    """Time-To-Live Cache implementation"""
    
    def __init__(self, capacity: int, default_ttl: float = 300.0):
        super().__init__(capacity)
        self._cache: Dict[Any, CacheItem] = {}
        self.default_ttl = default_ttl
        self._cleanup_thread = None
        self._start_cleanup_thread()
    
    def get(self, key: Any) -> Optional[Any]:
        """Get value if not expired"""
        with self._lock:
            if key not in self._cache:
                return None
            
            item = self._cache[key]
            
            # Check if expired
            if item.is_expired():
                del self._cache[key]
                self.size -= 1
                return None
            
            item.touch()
            return item.value
    
    def put(self, key: Any, value: Any, ttl: Optional[float] = None) -> None:
        """Put key-value pair with TTL"""
        with self._lock:
            if ttl is None:
                ttl = self.default_ttl
            
            # If key exists, update it
            if key in self._cache:
                self._cache[key].value = value
                self._cache[key].ttl = ttl
                self._cache[key].created_time = time.time()
                return
            
            # If at capacity, cleanup expired items first
            if self.size >= self.capacity:
                self._cleanup_expired()
                
                # If still at capacity, remove oldest item
                if self.size >= self.capacity:
                    self._evict_oldest()
            
            # Add new item
            item = CacheItem(key, value, ttl=ttl)
            self._cache[key] = item
            self.size += 1
    
    def delete(self, key: Any) -> bool:
        """Delete key from cache"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self.size -= 1
                return True
            return False
    
    def clear(self) -> None:
        """Clear all items"""
        with self._lock:
            self._cache.clear()
            self.size = 0
    
    def keys(self) -> List[Any]:
        """Get all non-expired keys"""
        with self._lock:
            self._cleanup_expired()
            return list(self._cache.keys())
    
    def _cleanup_expired(self) -> None:
        """Remove all expired items"""
        expired_keys = [key for key, item in self._cache.items() if item.is_expired()]
        for key in expired_keys:
            del self._cache[key]
            self.size -= 1
    
    def _evict_oldest(self) -> None:
        """Evict oldest item by creation time"""
        if self._cache:
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k].created_time)
            del self._cache[oldest_key]
            self.size -= 1
    
    def _start_cleanup_thread(self) -> None:
        """Start background thread for periodic cleanup"""
        def cleanup_worker():
            while True:
                time.sleep(30)  # Cleanup every 30 seconds
                with self._lock:
                    self._cleanup_expired()
        
        self._cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        self._cleanup_thread.start()


class MultiLevelCache:
    """Multi-level cache with different eviction policies per level"""
    
    def __init__(self, level_configs: List[Dict[str, Any]]):
        """
        Initialize multi-level cache
        level_configs: List of dicts with 'capacity', 'policy', and optional 'ttl'
        """
        self.levels: List[Cache] = []
        
        for config in level_configs:
            capacity = config['capacity']
            policy = config.get('policy', EvictionPolicy.LRU)
            ttl = config.get('ttl')
            
            if policy == EvictionPolicy.LRU:
                cache = LRUCache(capacity)
            elif policy == EvictionPolicy.LFU:
                cache = LFUCache(capacity)
            elif policy == EvictionPolicy.FIFO:
                cache = FIFOCache(capacity)
            elif policy == EvictionPolicy.TTL:
                cache = TTLCache(capacity, ttl or 300.0)
            else:
                cache = LRUCache(capacity)
            
            self.levels.append(cache)
    
    def get(self, key: Any) -> Optional[Any]:
        """Get value from any level, promoting to higher levels"""
        for i, level in enumerate(self.levels):
            value = level.get(key)
            if value is not None:
                # Promote to higher levels
                for j in range(i):
                    self.levels[j].put(key, value)
                return value
        return None
    
    def put(self, key: Any, value: Any, ttl: Optional[float] = None) -> None:
        """Put value in first level"""
        if self.levels:
            self.levels[0].put(key, value, ttl)
    
    def delete(self, key: Any) -> bool:
        """Delete from all levels"""
        deleted = False
        for level in self.levels:
            if level.delete(key):
                deleted = True
        return deleted
    
    def clear(self) -> None:
        """Clear all levels"""
        for level in self.levels:
            level.clear() 