from ..LSH.lsh_helpers import calculate_jaccard_similarity

# Given two keys in our similiar candidates graph, find their actual similiarity and use the double 
# linked link structure of each of our signatures to find the overall similiar region of code
def expand_similiarity_region(signatures, key1, key2, threshold, visited):
    current_key1 = key1
    current_key2 = key2
   
    # Find base similarity
    sig1 = signatures[key1]["signature"]
    sig2 = signatures[key2]["signature"]
    similiarity = calculate_jaccard_similarity(sig1, sig2)
    if similiarity < threshold:
        return None
    
    # Track all signature keys that are part of this region
    region_keys_file1 = []
    region_keys_file2 = []
    
    # Slide window upwards (previous lines)
    start_key1 = current_key1
    start_key2 = current_key2
    
    while True:
        prev_sig1 = signatures[current_key1]["prev_signature"]
        prev_sig2 = signatures[current_key2]["prev_signature"]

        if not prev_sig1 or not prev_sig2:
            break

        # Check similarity BEFORE updating current keys
        prev_similiarity = calculate_jaccard_similarity(
            signatures[prev_sig1]["signature"], 
            signatures[prev_sig2]["signature"]
        )
        
        if prev_similiarity < threshold:
            break
        
        # Only update if similarity is above threshold
        current_key1 = prev_sig1
        current_key2 = prev_sig2
        start_key1 = current_key1
        start_key2 = current_key2

    # Collect all keys from start to original position (going downward)
    temp_key1 = start_key1
    temp_key2 = start_key2
    while temp_key1 and temp_key2:
        region_keys_file1.append(temp_key1)
        region_keys_file2.append(temp_key2)
        if temp_key1 == key1 and temp_key2 == key2:
            break
        temp_key1 = signatures[temp_key1]["next_signature"]
        temp_key2 = signatures[temp_key2]["next_signature"]

    start_line_file_1 = signatures[start_key1]["original_line_number"]
    start_line_file_2 = signatures[start_key2]["original_line_number"]

    # Slide window downwards (next lines) - reset to original starting point
    current_key1 = key1
    current_key2 = key2
    end_key1 = current_key1
    end_key2 = current_key2

    while True:
        next_sig1 = signatures[current_key1]["next_signature"]
        next_sig2 = signatures[current_key2]["next_signature"]

        if not next_sig1 or not next_sig2:
            break

        # Check similarity BEFORE updating current keys
        next_similiarity = calculate_jaccard_similarity(
            signatures[next_sig1]["signature"], 
            signatures[next_sig2]["signature"]
        )

        if next_similiarity < threshold:
            break
        
        # Only update if similarity is above threshold
        current_key1 = next_sig1
        current_key2 = next_sig2
        end_key1 = current_key1
        end_key2 = current_key2
        
        # Add these keys to our region tracking
        region_keys_file1.append(current_key1)
        region_keys_file2.append(current_key2)

    end_line_file_1 = signatures[end_key1]["original_line_number"]
    end_line_file_2 = signatures[end_key2]["original_line_number"]

    # Mark ALL pairs in the expanded region as visited to prevent duplicates
    for key_f1 in region_keys_file1:
        for key_f2 in region_keys_file2:
            visited.add((key_f1, key_f2))
            visited.add((key_f2, key_f1))

    # return region of similiar code
    region = {
        "file1": signatures[key1]["file"],
        "file2": signatures[key2]["file"],
        "file1_start": start_line_file_1,
        "file2_start": start_line_file_2,
        "file1_end": end_line_file_1,
        "file2_end": end_line_file_2,
        "total_lines": max(end_line_file_1 - start_line_file_1 + 1, end_line_file_2 - start_line_file_2 + 1)
    }

    return region