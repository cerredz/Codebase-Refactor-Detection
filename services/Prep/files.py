from services.Prep.extensions import *
from collections import deque
import os

def get_invalid_file_paths():
    relative_path = "./hidden_filepaths.txt"
    absolute_path = os.path.abspath(relative_path)
    res = set()

    # read pre-defined hidden file-paths from the user
    with open(absolute_path, "r") as file:
        path = file.readline()
        abs_path = os.path.abspath(f"./codebase/{path}")
        res.add(abs_path)
    return res

def is_invalid_file_path(file_path: str):
    if os.path.exists(file_path):
        # handle file
        if not os.path.isdir(file_path):
            root, extension = os.path.splitext(file_path)
            is_invalid = file_path in get_invalid_file_paths() or extension in get_non_coding_files()
            return is_invalid
        # handle directory
        else:
            return file_path in get_invalid_file_paths()
    
    # file_path doesnt exist
    return True

def get_codebase_dir():
    codebase_dir = "./codebase"
    return os.path.abspath(codebase_dir)

def get_subfolders(abs_dir_path: str):
    if not os.path.exists(abs_dir_path) or not os.path.isdir(abs_dir_path):
        return []
    folder_paths = []
    for sub_path in os.listdir(abs_dir_path):
        new_path = os.path.join(abs_dir_path, sub_path)
        if os.path.isdir(new_path):
            folder_paths.append(new_path)
    return folder_paths

def get_subfiles(abs_file_path: str):
    if not os.path.exists(abs_file_path) or not os.path.isdir(abs_file_path):
        return []
    file_paths = []
    for sub_path in os.listdir(abs_file_path):
        new_path = os.path.join(abs_file_path, sub_path)
        if os.path.isfile(new_path):
            file_paths.append(new_path)
    return file_paths
    

def get_similiar_region_code(file1, file2, start1, end1, start2, end2):
    if not os.path.exists(file1) or not os.path.exists(file2):
        print("file not found")
        return []
    
    file1_code = ""
    with open(file1, "r", encoding="utf-8") as file:
        lines1 = file.readlines()
        for i in range(len(lines1)):
            line_number = i + 1
            if start1 <= line_number <= end1:
                file1_code += lines1[i]
    
    file2_code = ""
    with open(file2, "r", encoding="utf-8") as file:
        lines2 = file.readlines()
        for i in range(len(lines2)):
            line_number = i + 1
            if start2 <= line_number <= end2:
                file2_code += lines2[i]

    return {"file1": file1_code, "file2": file2_code}



    



