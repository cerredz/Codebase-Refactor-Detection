from collections import deque
from services.LSH.lsh import calculate_jaccard_similarity
from services.Similiarity.similiar_region_helpers import *
import heapq

def find_similiar_regions(signatures, adj_list, threshold = .85):
    idx = 1
    batch_size = 100
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

        key_file_name = key.split("_")[0]
        for similiar_key in values:
            similiar_key_file_name = similiar_key.split("_")[0]
            region_key = (key, similiar_key)
            if region_key not in visited and key_file_name != similiar_key_file_name:
                similiar_region = expand_similiarity_region(signatures, key, similiar_key, threshold)
                visited.add(region_key)
                #heapq.heappush(max_heap, (total_similiar_lines, (prev_key_sig1, prev_key_sig2, next_key_sig1, next_key_sig2)))

        

            #total_similiar_lines = end_line - start_line


    #highest_priority_task = heapq.heappop(max_heap)
    #print(highest_priority_task)

        







    
    

        
