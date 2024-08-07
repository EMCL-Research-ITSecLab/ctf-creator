"""
This module provides functions to work with tar archives. It includes functionalities 
to extract data from a tar archive to a specified destination directory and to create 
a tar archive from a source directory or list of files. When creating an archive, it 
includes only the files themselves without the folder structure and handles the deletion 
of an existing archive with the same name.

Functions:
  - untar_data(tar_file_path, destination_dir): Extracts data from a tar archive to a specified destination directory.
  - create_tar_archive(source_path, archive_name, compression=None): Creates a tar archive from a source directory or list of files.
"""

# Imports
import os
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

