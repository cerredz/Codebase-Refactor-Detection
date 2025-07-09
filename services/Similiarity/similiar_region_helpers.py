from services.LSH.lsh_helpers import calculate_jaccard_similarity

# Given two keys in our similiar candidates graph, find their actual similiarity and use the double 
# linked link structure of each of our signatures to find the overall similiar region of code
def expand_similiarity_region(signatures, key1, key2, threshold):
    current_key1 = key1
    current_key2 = key2
   
    # Find base similarity
    sig1 = signatures[key1]["signature"]
    sig2 = signatures[key2]["signature"]
    similiarity = calculate_jaccard_similarity(sig1, sig2)
    if similiarity < threshold:
        return None
    
    # Slide window upwards (previous lines)
    while True:
        prev_sig1 = signatures[current_key1]["prev_signature"]
        prev_sig2 = signatures[current_key2]["prev_signature"]

        if not prev_sig1 or not prev_sig2:
            break

        current_key1 = prev_sig1
        current_key2 = prev_sig2

        similiarity = calculate_jaccard_similarity(signatures[current_key1]["signature"], signatures[current_key2]["signature"])

        if similiarity < threshold:
            break

    start_line_file_1 = signatures[current_key1]["original_line_number"]
    start_line_file_2 = signatures[current_key2]["original_line_number"]

    # Slide window downwards (next lines)
    current_key1 = key1
    current_key2 = key2

    while True:
        next_sig1 = signatures[current_key1]["next_signature"]
        next_sig2 = signatures[current_key2]["next_signature"]

        if not next_sig1 or not next_sig2:
            break

        current_key1 = next_sig1
        current_key2 = next_sig2

        similiarity = calculate_jaccard_similarity(signatures[current_key1]["signature"], signatures[current_key2]["signature"])

        if similiarity < threshold:
            break

    end_line_file_1 = signatures[current_key1]["original_line_number"]
    end_line_file_2 = signatures[current_key2]["original_line_number"]

    # return region of similiar code
    region = {
        "file1": signatures[key1]["file"],
        "file2": signatures[key2]["file"],
        "file1_start": start_line_file_1,
        "file2_start": start_line_file_2,
        "file1_end": end_line_file_1,
        "file2_end": end_line_file_2,
        "total_lines": max(end_line_file_1 - start_line_file_1, end_line_file_2, start_line_file_2)
    }

    return region