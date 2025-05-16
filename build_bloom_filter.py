#!/usr/bin/env python3
"""Build a pre-computed bloom filter from ignore_commands.txt"""

import pickle
from pathlib import Path
from src.aiterm.bloom_filter import BloomFilter

def main():
    """Build and save a bloom filter from ignore_commands.txt"""
    src_dir = Path(__file__).parent / "src" / "aiterm"
    ignore_file = src_dir / "ignore_commands.txt"
    
    if not ignore_file.exists():
        print(f"ERROR: {ignore_file} not found. Run build_ignore_commands.py first.")
        return
    
    print(f"Building bloom filter from {ignore_file}")
    
    # Build bloom filter with very low false positive rate
    bf = BloomFilter.from_file(str(ignore_file), fp_prob=0.001)
    
    # Save the bloom filter data
    bloom_data = {
        'data': bf.to_bytes(),
        'size': bf.size,
        'hash_count': bf.hash_count
    }
    
    bloom_file = src_dir / "ignore_commands_bloom.pkl"
    with open(bloom_file, 'wb') as f:
        pickle.dump(bloom_data, f)
    
    print(f"Saved bloom filter to {bloom_file}")
    print(f"Bloom filter size: {bf.size} bits")
    print(f"Hash functions: {bf.hash_count}")
    
    # Test it works
    bf2 = BloomFilter.from_bytes(bloom_data['data'], bloom_data['size'], bloom_data['hash_count'])
    
    # Test some examples
    test_commands = ['2to3', 'FreeCAD', 'ls', 'cd', 'grep']
    print("\nTesting bloom filter:")
    for cmd in test_commands:
        in_original = cmd in bf
        in_loaded = cmd in bf2
        print(f"  {cmd}: original={in_original}, loaded={in_loaded}")

if __name__ == "__main__":
    main()