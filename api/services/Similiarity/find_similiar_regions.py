from collections import deque
from ..LSH.lsh_helpers import calculate_jaccard_similarity
from .similiar_region_helpers import *
import heapq

def find_similiar_regions(signatures, adj_list, region_threshold, threshold = .80):
    idx = 1
    batch_size = 1000
    batch_idx = 0
    total_batches = len(adj_list) // batch_size
    max_heap = []
    visited = set()

    for key, values in adj_list.items():
        idx += 1
        if idx % batch_size == 0:
            print(f"Batch processed ({batch_idx}/{total_batches})")
            batch_idx += 1
            idx = 0

        key_file_name = signatures[key]["file"]
        for similiar_key in values:
            similiar_key_file_name = signatures[similiar_key]["file"]
            region_key = (key, similiar_key)
            reverse_region_key = (similiar_key, key)
            if region_key not in visited and reverse_region_key not in visited and key_file_name != similiar_key_file_name:
                similiar_region = expand_similiarity_region(signatures, key, similiar_key, threshold, visited)
                if not similiar_region:
                    continue
                region_lines = similiar_region["total_lines"]
                # Note: visited keys are now handled inside expand_similiarity_region
                heapq.heappush(max_heap, (-region_lines, (similiar_region["file1"], similiar_region["file2"], similiar_region["file1_start"], similiar_region["file1_end"], similiar_region["file2_start"], similiar_region["file2_end"])))

    print(f"🟢 Found {len(max_heap)} regions of similiar code...")  
    top = heapq.heappop(max_heap)
    res = []
    while top and top[0] < region_threshold and max_heap: # values in heap are negative, less than
        res.append(top)
        top = heapq.heappop(max_heap)

    return res



    

        







    
    

        
