"""
Path utilities for the refactor analyzer project.
Provides consistent path resolution from any subdirectory.
"""
import os

def get_project_root():
    """
    Get the absolute path to the project root directory.
    Works from any subdirectory in the project.
    """
    # In Vercel deployment, everything is in /var/task
    # Get the directory of this file (api/services/Prep/paths.py)
    current_dir = os.path.dirname(__file__)
    # Go up three levels to get to project root (/var/task)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
    return os.path.abspath(project_root)

def get_codebase_path():
    """Get the absolute path to the codebase directory."""
    return os.path.join(get_project_root(), "codebase")

def get_config_path():
    """Get the absolute path to the config.json file."""
    return os.path.join(get_project_root(), "config.json")

def get_hidden_filepaths_path():
    """Get the absolute path to the hidden_filepaths.txt file."""
    return os.path.join(get_project_root(), "hidden_filepaths.txt")

def get_results_path():
    """Get the absolute path to the results.json file."""
    return os.path.join(get_project_root(), "results.json") 