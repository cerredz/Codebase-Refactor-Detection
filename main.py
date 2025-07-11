from services.Prep.codebase import *
from services.LSH.lsh import *
from services.Similiarity.find_similiar_regions import *
from services.Prep.read_config import *
from services.Prep.paths import get_results_path
import time
import json

if __name__ == "__main__":
    start = time.time()
    # read config file
    print("Reading config file...")
    config = read_config()

    # read codebase
    print("Running algorithm to suggest codbase refactors...")
    file_mappings = read_codebase() # normalized code of all files, mapping to original file index

    # find similiar lines using lsh
    print("Running the lsh algorithm for similiarity searching...")
    signatures, similiarity_adjacency_list = lsh(file_mappings, config["candidate_threshold"]) # run the lsh algorithm to hash similiar lines
    
    # find similiar regions using graph + sliding window
    print("Finding similiar regions of code...")
    region_threshold = -config["region_length"] # how many lines of code need to be similiar to determine a similiar region
    similiar_regions = find_similiar_regions(signatures, similiarity_adjacency_list, region_threshold, threshold=config["line_threshold"])
    res = []

    # actually get regions of code in similiar regions
    for region in similiar_regions:
        file1 = region[1][0]
        file2 = region[1][1]
        file1_start = region[1][2]
        file1_end = region[1][3]
        file2_start = region[1][4]
        file2_end = region[1][5]
        res.append({"regions": get_similiar_region_code(file1, file2, file1_start, file1_end, file2_start, file2_end), "file1": file1, "file2": file2})
    
    with open(get_results_path(), "w") as file:
        json.dump(res, file)

    end = time.time()
    total_time = end - start

    print(f"Found {len(res)} region/s of code greater than {-region_threshold} lines of code in {total_time} seconds. ")





    
    