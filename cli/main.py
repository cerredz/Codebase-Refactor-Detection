import argparse
import sys
import os
import subprocess

def main():
    """Main entry point for the refactor CLI."""
    # Parse arguments
    parser = argparse.ArgumentParser(description="Refactor analyzer CLI tool")
    
    # Create mutually exclusive group for commands
    command_group = parser.add_mutually_exclusive_group()
    
    # Add run command
    run_path = os.path.join(os.path.dirname(__file__), "run.py")
    command_group.add_argument('--run', nargs='?', const=run_path, default=None,
                              help="Run the refactor analysis (optionally specify script path)")
    
    # Add config command  
    config_script_path = os.path.join(os.path.dirname(__file__), "config.py")
    command_group.add_argument('--config', nargs='?', const=config_script_path, default=None,
                              help="View configuration (optionally specify script path)")
    
    # Add config file argument for when using --run
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.json")
    parser.add_argument('--config-file', type=str, default=config_path,
                       help="Path to config file (defaults to config.json)")
    
    # add report command
    report_script_file = os.path.join(os.path.dirname(__file__), "report.py")
    command_group.add_argument("--report", nargs='?', const=report_script_file, default=None, 
                               help="View results.")


    args = parser.parse_args()
    
    # Determine which script to run
    script_to_run = None
    if args.run is not None:
        script_to_run = args.run
    elif args.config is not None:
        script_to_run = args.config
    elif args.report is not None:
        script_to_run = args.report
    else:
        # Default to run if no command specified
        script_to_run = run_path

    # Execute the script
    try:
        print(f"Executing: {script_to_run}")
        
        # Get the project root directory (parent of cli/)
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Set up environment with project root in PYTHONPATH
        env = os.environ.copy()
        if 'PYTHONPATH' in env:
            env['PYTHONPATH'] = project_root + os.pathsep + env['PYTHONPATH']
        else:
            env['PYTHONPATH'] = project_root
        
        # Set config file path if this is a run command
        if args.run is not None:
            env['REFACTOR_CONFIG_PATH'] = args.config_file
        
        result = subprocess.run([sys.executable, script_to_run], 
                              cwd=project_root,  
                              env=env, 
                              check=True)
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"Error executing {script_to_run}: {e}")
        return e.returncode
    except FileNotFoundError:
        print(f"Error: Script not found: {script_to_run}")
        return 1

if __name__ == "__main__":
    sys.exit(main())