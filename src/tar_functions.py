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

def create_tar_archive(source_path, archive_name, compression=None):
  """
  Creates a tar archive (TAR file) from a source directory or list of files,
  extracting only the files themselves without the folder structure,
  deleting an existing archive with the same name.

  Args:
    source_path (str): Path to the directory or list of files to be archived.
    archive_name (str): Desired filename for the tar archive.
    compression (str, optional): Compression method (None for no compression, 'gzip' for gzip, 'bzip2' for bzip2).
  """
  try:
    # Open the tar archive in write mode (with compression if specified)
    if compression:
      mode = f"w:{compression}"
    else:
      mode = "w"

    # Check for existing archive and delete if necessary
    if os.path.exists(archive_name):
      os.remove(archive_name)
      print(f"Existing archive '{archive_name}' deleted.")

    with tarfile.open(archive_name, mode) as tar:
      # Add files without folder structure
      if os.path.isdir(source_path):
        # Extract filenames from the directory structure
        for root, _, files in os.walk(source_path):
          for file in files:
            file_path = os.path.join(root, file)
            # Use os.path.basename to get the filename without the path
            tar.add(file_path, arcname=os.path.basename(file_path))
      else:
        # Handle single file or list of files
        if isinstance(source_path, list):
          for file_path in source_path:
            tar.add(file_path, arcname=os.path.basename(file_path))
        else:
          tar.add(source_path, arcname=os.path.basename(source_path))

      print(f"Tar archive '{archive_name}' created successfully (files only).")
  except Exception as e:
    print(f"Error creating tar archive: {e}")
