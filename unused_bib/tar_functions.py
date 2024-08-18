"""
This module provides functions to work with tar archives. It includes functionalities 
to extract data from a tar archive to a specified destination directory. 

Functions:
  - untar_data(tar_file_path, destination_dir): Extracts data from a tar archive to a specified destination directory.
"""

#!!! Brauche ich diese funktion überhaupt?
#!!! Checkde den code ob da nicht unnötig ist! Spart dir auch die tests dazu!
# Imports
import tarfile

def untar_data(tar_file_path, destination_dir):
  """
  Extracts data from a tar archive to a specified destination directory.

  Args:
    tar_file_path (str): Path to the tar archive file.
    destination_dir (str): Path to the directory where extracted files will be placed.
  """
  try:
    # Open the tar archive in read mode
    with tarfile.open(tar_file_path, "r") as tar:
      # Extract all files to the destination directory
      tar.extractall(destination_dir)
      print(f"Data extracted from {tar_file_path} to {destination_dir}")
  except tarfile.ReadError as e:
    print(f"Error reading tar file: {e}")
  except tarfile.TarError as e:
    print(f"Error extracting tar archive: {e}")
  except FileNotFoundError:
    print(f"Error: File '{tar_file_path}' not found.")

