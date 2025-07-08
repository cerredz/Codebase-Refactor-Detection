from services.LSH.lsh_helpers import *
import numpy as np

def lsh(file_mapping: dict):
    # 1) Create our global shingle set
    union = set()
    for keys, values in file_mapping.items():
        code_lines = values["code"]
        for line in code_lines:
            line_shingle_set = generate_shingle_set(line)
            if line_shingle_set is not None:
                union.update(line_shingle_set)


    # 2) Convert union to list for consistent indexing
    shingle_list = list(union)
    shingle_index_map = {shingle: idx for idx, shingle in enumerate(shingle_list)}

    # 3) Hash functions
    num_hash_functions = 100
    hash_functions = generate_hash_functions(num_hash_functions, len(shingle_list))

    # 4) Build signature matrix
    signatures  = {}
    for file_key, file_data in file_mapping.items():
        code_lines = file_data["code"]
        original_lines = file_data["line_mapping"]

        for line_idx, line in enumerate(code_lines):
            line_shingle_set = generate_shingle_set(line)
            
            if line_shingle_set is not None:
                signature = create_signature(line_shingle_set, shingle_index_map, hash_functions)

                # Store with metadata
                fingerprint_id = f"{file_key}_{line_idx}"
                prev_id = f"{file_key}_{line_idx - 1}" if line_idx > 0 else None
                next_id = f"{file_key}_{line_idx + 1}" if line_idx < len(code_lines) - 1 else None

                signatures[fingerprint_id] = {
                    'signature': signature,
                    'file': file_key,
                    'line_number': line_idx,
                    'original_line': line,
                    'original_line_number': original_lines[line_idx],
                    'next_signature': next_id,
                    'prev_signature': prev_id
                }

    import json
    print(json.dumps(signatures, indent=2))
    return 0