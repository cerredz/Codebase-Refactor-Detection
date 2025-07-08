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








if __name__ == "__main__":
    print(generate_shingle_set("print(hello world)"))

