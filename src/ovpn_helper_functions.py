
import subprocess
import os
import time



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
      time.sleep(3)
      curl_client_ovpn_file_version(container, host_address, user_name, counter, save_path, max_retries_counter)
    else:
      print(f"Download failed after {max_retries} retries. Exiting.")
      exit(1)

  except Exception as e:
    print(f"Error: An unexpected error occurred - {e}")
    if max_retries_counter < max_retries:
      print(f"Retrying download (attempt {max_retries_counter+1} of {max_retries})")
      max_retries_counter +=1
      time.sleep(3)
      curl_client_ovpn_file_version(container, host_address, user_name, counter, save_path, max_retries_counter)
    else:
      print(f"Download failed after {max_retries} retries. Exiting. There might be a problem with the host")
      exit(1)


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
          modified_lines.append(f"route {new_route_ip}\n")
      else:
          modified_lines.append(line)

  if not remote_line_found:
      print("No 'remote' line found in the file.")
      return

  with open(file_path, 'w') as file:
      file.writelines(modified_lines)