from .normalizer import *
from .files import *

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
        if code and line_mapping:
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