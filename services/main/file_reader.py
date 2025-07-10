from services.Prep.normalizer import *
from services.Prep.files import *
from services.LSH.lsh import *
from services.Similiarity.find_similiar_regions import *
import json

# Helper function for reading the codebase, reads all of the files in a directory, then recursively reads files in subdirectories
def read_dir(current_path: str):
    # Skip file paths that user wants hidden
    if current_path in get_invalid_file_paths():
        pass
    
    file_mappings = {}
    sub_folders = get_subfolders(current_path)
    sub_files = get_subfiles(current_path)

    # Add current sub-files
    for file in sub_files:
        code, line_mapping = normalize_file_path(file)
        file_mappings[file] = {"code": code, "line_mapping": line_mapping}

    # repeat process for subfolders
    for sub_folder in sub_folders:
        file_mappings.update(read_dir(sub_folder))

    return file_mappings

# Read the codebase
def read_codebase():
    print("Reading codebase...")
    abs_codebase_path = get_codebase_dir()
    file_mappings = read_dir(abs_codebase_path)
    print(f"🟢 Found {len(file_mappings)} files inside of the codebase.")
    print(f"🟢 Codebase contains {sum(len(file_data['code']) for file_data in file_mappings.values())} lines of code after normalizing.")
    return file_mappings

if __name__ == "__main__":
    # read codebase
    print("Running algorithm to suggest codbase refactors...")
    file_mappings = read_codebase() # normalized code of all files, mapping to original file index

    # find similiar lines using lsh
    print("Running the lsh algorithm for similiarity searching...")
    signatures, similiarity_adjacency_list = lsh(file_mappings) # run the lsh algorithm to hash similiar lines
    
    # find similiar regions using graph + sliding window
    print("Finding similiar regions of code...")
    region_threshold = -25 # how many lines of code need to be similiar to determine a similiar region
    similiar_regions = find_similiar_regions(signatures, similiarity_adjacency_list, region_threshold)
    res = []

    # actually regions of code in similiar regions
    for region in similiar_regions:
        file1 = region[1][0]
        file2 = region[1][1]
        file1_start = region[1][2]
        file1_end = region[1][3]
        file2_start = region[1][4]
        file2_end = region[1][5]
        res.append(get_similiar_region_code(file1, file2, file1_start, file1_end, file2_start, file2_end))
    
    print(res)



    
    