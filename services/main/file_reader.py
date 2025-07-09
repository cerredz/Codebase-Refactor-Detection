from services.Prep.normalizer import *
from services.Prep.files import *
from services.LSH.lsh import *
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
    abs_codebase_path = get_codebase_dir()
    file_mappings = read_dir(abs_codebase_path)
    return file_mappings

if __name__ == "__main__":
    file_mappings = read_codebase() # normalized code of all files, mapping to original file index
    lsh = lsh(file_mappings) # run the lsh algorithm to hash similiar lines
    #print(json.dumps(lsh, indent=2))