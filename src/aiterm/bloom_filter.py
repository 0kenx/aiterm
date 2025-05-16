"""Bloom filter implementation for command filtering."""

import math
import mmh3
from bitarray import bitarray


class BloomFilter:
    """Simple Bloom filter implementation using MurmurHash3."""
    
    def __init__(self, items_count, fp_prob=0.01):
        """
        Initialize bloom filter.
        
        Args:
            items_count: Expected number of items to store
            fp_prob: False positive probability (default 0.01 = 1%)
        """
        # Calculate optimal size and hash functions
        self.size = self.get_size(items_count, fp_prob)
        self.hash_count = self.get_hash_count(self.size, items_count)
        self.bit_array = bitarray(self.size)
        self.bit_array.setall(0)
    
    @staticmethod
    def get_size(n, p):
        """Calculate optimal bit array size."""
        m = -(n * math.log(p)) / (math.log(2) ** 2)
        return int(m)
    
    @staticmethod
    def get_hash_count(m, n):
        """Calculate optimal number of hash functions."""
        k = (m / n) * math.log(2)
        return int(k)
    
    def add(self, item):
        """Add an item to the filter."""
        digests = []
        for i in range(self.hash_count):
            # Create different hash values using seed
            digest = mmh3.hash(item, i) % self.size
            digests.append(digest)
            self.bit_array[digest] = True
    
    def contains(self, item):
        """Check if an item might be in the filter."""
        for i in range(self.hash_count):
            digest = mmh3.hash(item, i) % self.size
            if self.bit_array[digest] == False:
                return False
        return True
    
    def __contains__(self, item):
        """Allow 'in' operator."""
        return self.contains(item)
    
    @classmethod
    def from_file(cls, filename, fp_prob=0.01):
        """Create bloom filter from a file of items."""
        # Read items from file
        with open(filename, 'r') as f:
            items = [line.strip() for line in f if line.strip()]
        
        # Create bloom filter
        bf = cls(len(items), fp_prob)
        
        # Add all items
        for item in items:
            bf.add(item)
        
        return bf
    
    def to_bytes(self):
        """Convert bloom filter to bytes for saving."""
        return self.bit_array.tobytes()
    
    @classmethod
    def from_bytes(cls, data, size, hash_count):
        """Recreate bloom filter from bytes."""
        bf = cls.__new__(cls)
        bf.size = size
        bf.hash_count = hash_count
        bf.bit_array = bitarray()
        bf.bit_array.frombytes(data)
        return bf


# Global bloom filter instance (will be loaded at import time)
_bloom_filter = None

def get_bloom_filter():
    """Get the global bloom filter instance."""
    global _bloom_filter
    if _bloom_filter is None:
        import os
        import pickle

        # Try to load pre-computed bloom filter first
        bloom_file = os.path.join(os.path.dirname(__file__), 'ignore_commands_bloom.pkl')
        if os.path.exists(bloom_file):
            try:
                with open(bloom_file, 'rb') as f:
                    bloom_data = pickle.load(f)
                _bloom_filter = BloomFilter.from_bytes(
                    bloom_data['data'],
                    bloom_data['size'],
                    bloom_data['hash_count']
                )
                return _bloom_filter
            except Exception:
                pass  # Fall back to building from text file

        # Fall back to building from text file
        ignore_file = os.path.join(os.path.dirname(__file__), 'ignore_commands.txt')
        if os.path.exists(ignore_file):
            _bloom_filter = BloomFilter.from_file(ignore_file, fp_prob=0.001)  # 0.1% false positive rate
        else:
            # No ignore file, create empty bloom filter
            _bloom_filter = BloomFilter(0, 0.001)

    return _bloom_filter

def should_ignore_command(command):
    """Check if a command should be ignored."""
    bf = get_bloom_filter()
    # Handle special case for commands starting with .
    if command.startswith('.'):
        return True
    return command in bf