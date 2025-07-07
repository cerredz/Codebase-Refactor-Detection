from services.Prep.normalizer import *
from services.Prep.files import *

def read_files():
    abs_codebase_path = get_codebase_dir()
    current_path = abs_codebase_path

    while current_path:
        sub_folders = get_subfolders(current_path)
        sub_files = get_subfiles(current_path)

        for file in sub_files:
            normalize_file_path(file)

        break


    

    



if __name__ == "__main__":
    read_files()