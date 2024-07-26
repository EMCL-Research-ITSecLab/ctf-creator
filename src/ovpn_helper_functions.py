
import subprocess
import os
import time

def curl_client_ovpn_zip_version(container, host_address, user_name, counter, save_path, max_retries_counter=0, max_retries=10):
  """
  Downloads a .zip version of the client OpenVPN configuration file.

  Args:
    container: Docker container object (unused in this function but kept for consistency).
    host_address (str): Address of the host serving the file.
    user_name (str): Name of the user.
    counter (int): Counter for port calculation.
    save_path (str): Path to the directory where the file will be saved.
    max_retries_counter (int, optional): Current retry attempt count.
    max_retries (int, optional): Maximum number of retry attempts.
  """
  save_directory = f"{save_path}/data/{user_name}"
  #!!! Was passiert, wenn ich über Portnr hochzähle
  url = f"http://{host_address}:{80 + counter}"

  try:
    # Ensure the save directory exists; create it if not
    os.makedirs(save_directory, exist_ok=True)

    # Construct the command to download the file using curl
    command = f"curl -o {save_directory}/client.zip {url}"

    # Run the command using subprocess
    subprocess.run(command, shell=True, check=True)
    
    print(f"File downloaded successfully to {save_directory}/client.zip")

  except subprocess.CalledProcessError as e:
    print(f"Error: Failed to download file. Command returned non-zero exit status ({e.returncode})")

    if max_retries_counter < max_retries:
      print(f"Retrying download (attempt {max_retries_counter+1} of {max_retries})")
      max_retries_counter +=1
      exit_code, output = container.exec_run("./genclient.sh z", detach=True)
      time.sleep(3)
      curl_client_ovpn_zip_version(container, host_address, user_name, counter, save_path, max_retries_counter)
    else:
      print(f"Download failed after {max_retries} retries. Exiting.")
      exit(1)

  except Exception as e:
    print(f"Error: An unexpected error occurred - {e}")
    if max_retries_counter < max_retries:
      print(f"Retrying download (attempt {max_retries_counter+1} of {max_retries})")
      max_retries_counter +=1
      exit_code, output = container.exec_run("./genclient.sh z", detach=True)
      time.sleep(3)
      curl_client_ovpn_zip_version(container, host_address, user_name, counter, save_path, max_retries_counter)
    else:
      print(f"Download failed after {max_retries} retries. Exiting. There might be a problem with the host")
      exit(1)

def curl_client_ovpn_file_version(container, host_address, user_name, counter, save_path, max_retries_counter=0, max_retries=10):
  """
  Downloads a .conf version of the client OpenVPN configuration file.

  Args:
    container: Docker container object (unused in this function but kept for consistency).
    host_address (str): Address of the host serving the file.
    user_name (str): Name of the user.
    counter (int): Counter for port calculation.
    save_path (str): Path to the directory where the file will be saved.
    max_retries_counter (int, optional): Current retry attempt count.
    max_retries (int, optional): Maximum number of retry attempts.
  """
  save_directory = f"{save_path}/data/{user_name}"
  url = f"http://{host_address}:{80 + counter}"

  try:
    # Ensure the save directory exists; create it if not
    os.makedirs(save_directory, exist_ok=True)

    # Construct the command to download the file using curl
    command = f"curl -o {save_directory}/client.ovpn {url}"

    # Run the command using subprocess
    subprocess.run(command, shell=True, check=True)
    
    print(f"File downloaded successfully to {save_directory}/client.ovpn")

  except subprocess.CalledProcessError as e:
    print(f"Error: Failed to download file. Command returned non-zero exit status ({e.returncode})")

    if max_retries_counter < max_retries:
      print(f"Retrying download (attempt {max_retries_counter+1} of {max_retries})")
      max_retries_counter +=1
      curl_client_ovpn_file_version(container, host_address, user_name, counter, save_path, max_retries_counter)
    else:
      print(f"Download failed after {max_retries} retries. Exiting.")
      exit(1)

  except Exception as e:
    print(f"Error: An unexpected error occurred - {e}")
    if max_retries_counter < max_retries:
      print(f"Retrying download (attempt {max_retries_counter+1} of {max_retries})")
      max_retries_counter +=1
      curl_client_ovpn_file_version(container, host_address, user_name, counter, save_path, max_retries_counter)
    else:
      print(f"Download failed after {max_retries} retries. Exiting. There might be a problem with the host")
      exit(1)

def modify_server_conf(filename, comment_char="#", new_push_route="10.13.0.0 255.255.255.0"):
  """
  Modifies a file by commenting out existing "push route" lines and adding a new one after the last push.

  Args:
    filename (str): Path to the file to modify.
    comment_char (str, optional): Character to prepend to comment out lines (defaults to "#").
    new_push_route (str, optional): The new "push route" line to be added (defaults to "10.13.0.0 255.255.255.0").

  Returns:
    bool: True if the file was modified successfully, False otherwise.
  """
  try:
    with open(filename, "r+") as f:
      content = f.readlines()
      modified_lines = []
      last_push_index = None  # Initialize to None

      for i, line in enumerate(content):
        if line.startswith("push"):
          modified_lines.append(f"{comment_char} {line}")
          last_push_index = i  # Update index only when encountering a push line
        else:
          modified_lines.append(line)

      # Insert the new push route line after the last existing push (if any)
      if last_push_index is not None:
        modified_lines.insert(last_push_index + 1, f"""push "route {new_push_route}"\n""")
      else:
        # No existing push route, append to the end
        modified_lines.append(f"""push "route {new_push_route}"\n""")

      f.seek(0)
      f.writelines(modified_lines)
      return True
  except FileNotFoundError:
    print(f"Error: File '{filename}' not found.")
    return False
  except Exception as e:
    print(f"Error modifying file: {e}")
    return False


#!!! Bug adds 255.255.255.0 twice! in client file!
def modify_ovpn_file(file_path, new_port, new_route_ip):
  if not os.path.exists(file_path):
      print(f"File {file_path} does not exist.")
      return

  modified_lines = []

  with open(file_path, 'r') as file:
      lines = file.readlines()

  remote_line_found = False

  for line in lines:
      if line.startswith("remote "):
          parts = line.split()
          if len(parts) == 3:
              parts[-1] = str(new_port)
              line = " ".join(parts) + "\n"
              remote_line_found = True

          modified_lines.append(line)
          modified_lines.append("route-nopull\n")
          modified_lines.append(f"route {new_route_ip} 255.255.255.0\n")
      else:
          modified_lines.append(line)

  if not remote_line_found:
      print("No 'remote' line found in the file.")
      return

  with open(file_path, 'w') as file:
      file.writelines(modified_lines)