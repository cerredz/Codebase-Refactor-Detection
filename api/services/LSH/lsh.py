from services.LSH.lsh_helpers import *
import numpy as np
import json

def lsh(file_mapping: dict, candidate_threshold: float):
    # 1) Create our global shingle set
    union = set()
    for keys, values in file_mapping.items():
        code_lines = values["code"]
        for line in code_lines:
            line_shingle_set = generate_shingle_set(line)
            if line_shingle_set is not None:
                union.update(line_shingle_set)
    
    print("🟢 Created global shingle set. (1/7)")
    # 2) Convert union to list for consistent indexing
    shingle_list = list(union)
    shingle_index_map = {shingle: idx for idx, shingle in enumerate(shingle_list)}
    print("🟢 Converted global shingle set to union for consistent indexing. (2/7)")

    # 3) Hash functions
    num_hash_functions = 100
    hash_functions = generate_hash_functions(num_hash_functions, len(shingle_list))
    print("🟢 Generated hash functions. (3/7)")

    # 4) Build signature matrix
    signatures = {}
    signature_keys_by_file = {}  # Track which line indices have signatures for each file

    for file_key, file_data in file_mapping.items():
        code_lines = file_data["code"]
        original_lines = file_data["line_mapping"]
        signature_keys_by_file[file_key] = []

        for line_idx, line in enumerate(code_lines):
            line_shingle_set = generate_shingle_set(line)
            
            if line_shingle_set is not None:
                signature = create_signature(line_shingle_set, shingle_index_map, hash_functions)
                fingerprint_id = f"{file_key}_{line_idx}"
                signature_keys_by_file[file_key].append((line_idx, fingerprint_id))

                signatures[fingerprint_id] = {
                    'signature': signature,
                    'file': file_key,
                    'line_number': line_idx,
                    'original_line': line,
                    'original_line_number': original_lines[line_idx],
                    'next_signature': None,  # Will be set in next step
                    'prev_signature': None   # Will be set in next step
                }

    # Now create the proper links between existing signatures
    for file_key, line_data in signature_keys_by_file.items():
        for i, (line_idx, fingerprint_id) in enumerate(line_data):
            # Set previous signature link
            if i > 0:
                prev_fingerprint_id = line_data[i-1][1]
                signatures[fingerprint_id]['prev_signature'] = prev_fingerprint_id
            
            # Set next signature link  
            if i < len(line_data) - 1:
                next_fingerprint_id = line_data[i+1][1]
                signatures[fingerprint_id]['next_signature'] = next_fingerprint_id

    print("🟢 Built signature matrix. (4/7)")

    # 5) Create buckets for banding
    banding = create_band_buckets(signatures, 10)
    print("🟢 Created buckets for banding. (5/7)")
    
    # 6) Find candidates from the same buckets
    candidates = set()

    for band_idx, buckets in banding.items():
        for band_key, fingerprint_ids in buckets.items():
            # found candidates, add all combinations of them to candidates
            if len(fingerprint_ids) > 1:
                for i in range(len(fingerprint_ids)):
                    for j in range(i + 1, len(fingerprint_ids)):
                        candidates.add((fingerprint_ids[i], fingerprint_ids[j]))
                        candidates.add((fingerprint_ids[j], fingerprint_ids[i]))
    print("🟢 Found potential candidates. (6/7)")

    # 7) Using candidates, find the actual similiar ones
    similiarity_threshold = candidate_threshold
    similiarity_adjacency_list = {}

    for candidate_pair in candidates:
        if len(candidate_pair) == 2:
            id1, id2 = candidate_pair
            sig1 = signatures[id1]["signature"]
            sig2 = signatures[id2]["signature"]

            similarity = calculate_jaccard_similarity(sig1, sig2)

            if similarity > similiarity_threshold:
                # create connection in graph if above similiarity threshold
                if id1 not in similiarity_adjacency_list:
                    similiarity_adjacency_list[id1] = []

                if id2 not in similiarity_adjacency_list:
                    similiarity_adjacency_list[id2] = []

                similiarity_adjacency_list[id1].append(id2)
                similiarity_adjacency_list[id2].append(id1)

    print("🟢 Found similiar fingerprints. (7/7)")
    return signatures, similiarity_adjacency_list  