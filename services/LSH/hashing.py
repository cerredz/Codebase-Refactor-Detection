
def generate_shingle_set(code: str, k = 5):
    shingles = set()
    idx = 0
    if len(code) > k:
        for idx in range(len(code) - k + 1):
            shingles.add(code[idx:idx + k])
        return shingles

    # length of code is shorter than k
    return None

