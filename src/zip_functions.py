"""
This module provides functionalities for zipping folders.

The main functionalities include:
1. Zipping all files in a specified folder and storing the resulting zip file at a specified path.

Functions:
- zip_folder(folder_path, zip_path): Zips all files in a folder and stores the zip file at the given path.
"""
import zipfile
import os

def zip_folder(folder_path, zip_path):
    """
    Zips all files in a folder and stores the zip file at a specified path. This is useful for zipping files that are in a different directory than the one being zipped.
    
    Args:
        folder_path: The path to the folder to zip.
        zip_path: The path to the zip file to create.
    """
    # Expand the user's home directory in the folder and zip paths
    folder_path = os.path.expanduser(folder_path)
    zip_path = os.path.expanduser(zip_path)
    
    # Create a ZipFile object in write mode
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Iterate over all the files in the folder
        # Add all files to the zip archive
        for root, dirs, files in os.walk(folder_path):
            # Add the files to the zip archive
            for file in files:
                # Get the full path of the file
                file_path = os.path.join(root, file)
                # Add the file to the zip archive with relative path
                zipf.write(file_path, os.path.relpath(file_path, folder_path))
