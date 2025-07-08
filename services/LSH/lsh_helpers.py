import hashlib

def generate_shingle_set(code: str, k = 5):
    shingles = set()
    idx = 0
    if len(code) > k:
        for idx in range(len(code) - k + 1):
            shingles.add(code[idx:idx + k])
        return shingles

    # length of code is shorter than k
    return None

def generate_hash_functions(n: int, shingle_len: int):
    hex_dash = None
    for i in range(n):
        hasher = hashlib.sha256()
        hasher.update(shingle_len)
        hex_dash = hasher.hexdigest()
    
    return hex_dash

def create_signature(shingle_set: set, shingle_list: list, hash_functions: function):
    pass




if __name__ == "__main__":
    print(generate_shingle_set("print(hello world)"))

