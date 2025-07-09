import hashlib
from random import shuffle

# Generates a shingle set for a line of code
def generate_shingle_set(code: str, k = 5):
    shingles = set()
    idx = 0
    if len(code) > k:
        for idx in range(len(code) - k + 1):
            shingles.add(code[idx:idx + k])
        return shingles

    # length of code is shorter than k
    return None

# Generates the hash functions for lsh
def generate_hash_functions(n: int, shingle_len: int):
    hash_functions = []

    # Create a random permutation of indices 0 to shingle_len-1
    for i in range(n):
        permutation = list(range(shingle_len))
        shuffle(permutation)
        hash_functions.append(permutation)
    
    return hash_functions

# Generates the signature of a line of code for lsh
def create_signature(shingle_set: set, shingle_index_map: list, hash_functions):
    shingle_indices = [shingle_index_map[shingle] for shingle in shingle_set if shingle in shingle_index_map]
    if not shingle_indices:
        return [len(hash_functions[0])] * len(hash_functions)
    
    signature = []
    for hash_func in hash_functions:
        min_hash = min(hash_func[idx] for idx in shingle_indices)
        signature.append(min_hash)
    
    return signature

# Splitting a vector into buckets of size b (need for banding in lsh)
def split_vector(signature: list, b: int):
    assert len(signature) % b == 0
    sub_size = int(len(signature) // b)
    return [signature[i:i + sub_size] for i in range(0, len(signature), sub_size)]

# Creates the buckets for the lsh algorithm
def create_band_buckets(signatures, num_bands):
    band_buckets = {}
    for fingerprint_id, fingerprint_data in signatures.items():
        sig = fingerprint_data["signature"]
        bands = split_vector(sig, num_bands)
        
        for band_idx, band in enumerate(bands):
            band_key = tuple(band)
            if band_idx not in band_buckets:
                band_buckets[band_idx] = {}
            
            if band_key not in band_buckets[band_idx]:
                band_buckets[band_idx][band_key] = []
        
            band_buckets[band_idx][band_key].append(fingerprint_id)
    
    return band_buckets

#  Calculate Jaccard similarity between two signatures
def calculate_jaccard_similarity(sig1, sig2):
    
    if len(sig1) != len(sig2):
        return 0.0
    
    matches = sum(1 for a, b in zip(sig1, sig2) if a == b)
    return matches / len(sig1) 


if __name__ == "__main__":
    print(generate_shingle_set("print(hello world)"))

