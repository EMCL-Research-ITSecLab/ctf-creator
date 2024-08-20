"""
This module provides functionality to validate file paths and ensure they meet specific criteria.

The main functionality includes:

1. Validating a directory path intended for saving user data.
2. Validating a configuration file path to ensure it is a valid YAML file.

Functions:
- validate_save_path(ctx, param, value): Validates the provided save path, ensuring it is a valid directory path. If the path does not exist, it attempts to create it. Raises an error if the path is invalid or cannot be created.
- validate_yaml_file(ctx, param, value): Validates the provided configuration file path. Ensures the file exists, is a valid file (not a directory), has a .yaml or .yml extension, and contains valid YAML content. Raises an error if any of these conditions are not met.
"""

import os
import click
import yaml

def validate_save_path(ctx, param, value):
    """
    Validate the save_path provided by the user.
    Ensure it's a valid path where a directory can be created.
    """
    # Check if the path already exists
    if os.path.exists(value):
        # If it exists, ensure it's a directory
        if not os.path.isdir(value):
            raise click.BadParameter(f"The path '{value}' is not a directory.")
    else:
        # If it doesn't exist, check if the directory can be created
        try:
            os.makedirs(value, exist_ok=True)
        except Exception as e:
            raise click.BadParameter(f"The path '{value}' is invalid: {e}")

    return value


def validate_yaml_file(ctx, param, value):
    """
    Validate the config file path provided by the user.s
    Ensure it's a valid YAML file with the correct extension.
    """
    # Check if the path exists
    if not os.path.exists(value):
        raise click.BadParameter(f"The file '{value}' does not exist.")
    
    # Check if it's a file (not a directory)
    if not os.path.isfile(value):
        raise click.BadParameter(f"The path '{value}' is not a file.")
    
    # Check if the file has a .yaml or .yml extension
    if not (value.endswith('.yaml') or value.endswith('.yml')):
        raise click.BadParameter("The file must have a .yaml or .yml extension.")
    
    # Try to load the file using a YAML parser to ensure it's a valid YAML
    try:
        with open(value, 'r') as file:
            yaml.safe_load(file)
    except yaml.YAMLError as exc:
        raise click.BadParameter(f"The file '{value}' is not a valid YAML file: {exc}")
    
    return value