import os

# Normalizes files, makes sure that we are only fingerprinting the actual code
def normalize_file_path(abs_file_path: str):
    code = []
    line_mapping = []  
    try:
        with open(abs_file_path, "r", encoding="utf-8") as file:
            in_multiline_string = False
            original_line_number = 0
            
            for line in file:
                original_line_number += 1
                # Make sure we are only handling code lines 
                if not is_import(line) and not is_comment(line) and not is_decorator(line) and not is_empty_line(line):
                    
                    # Check if we are in a multiline string 
                    if is_multiline_string(line):
                        in_multiline_string = not in_multiline_string

                    if not in_multiline_string and not is_multiline_string(line):
                        # Make sure we are not in multiline string or at the closing point of it
                        normalized_line = line.lstrip()
                        code.append(normalized_line)
                        line_mapping.append(original_line_number)
    except Exception as e:
        return [None, None]

    return code, line_mapping

def is_import(code: str):
    return code.lstrip().startswith("from") or code.lstrip().startswith("import")

def is_comment(code: str):
    return code.lstrip().startswith("#") or code.lstrip().startswith('"""')

def is_multiline_string(code: str):
    return code.lstrip().startswith("'")

def is_decorator(code: str):
    return code.lstrip().startswith("@")

def is_empty_line(code: str):
    return len(code.strip()) == 0