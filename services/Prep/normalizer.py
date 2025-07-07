import os

def normalize_file_path(abs_file_path: str):
    file = ""
    with open(abs_file_path, "w") as f:
        file = f.read()
        print(file)

def remove_comments(code: str):
    pass

def remove_imports(code: str):
    pass

def rename_variables(code: str):
    pass