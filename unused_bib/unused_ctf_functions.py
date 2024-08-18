# Example to create a Jump Host but it it currently not used!
#doc.create_jump_host(docker_client,network_name,user_name,f"{subnet_first_part[0]}.{subnet_second_part[0]}.{subnet_base}.2",k,hosts[current_vm-1])

#!!! Bug in create split VPN test it does not chang the other server conf it a different folder!
#doc.create_split_vpn_on_host(docker_client,user_name,new_push_route,save_path,k)

#!!! To mount the data correctly need to send the data to the host!!! make sure it funtionkioert bugfree
        #!!! better send a python script per ssh and start it?!
        #!!! change the mount folder in start ovpn with old data!
        #hosts_func.execute_ssh_command(hosts[current_vm-1],"mkdir download_dockovpn_data")
        #hosts_func.send_tar_file_via_ssh(f"{save_path}/data/{user_name}/dockovpn_data.tar",hosts[current_vm-1],"/home/ubuntu/download_dockovpn_data/dockovpn_data.tar")
        #hosts_func.execute_ssh_command(hosts[current_vm-1],"tar -xvf /home/ubuntu/download_dockovpn_data/dockovpn_data.tar -f")
        #hosts_func.execute_ssh_command(hosts[current_vm-1],f"sudo rm -r ctf-data" )
        #hosts_func.send_and_extract_tar_via_ssh_v2(f"{save_path}/data/{user_name}/dockovpn_data.tar",extracted_hosts_username[current_vm-1],extracted_hosts[current_vm-1],f"/home/{extracted_hosts_username[current_vm-1]}/ctf-data/{user_name}/dock_vpn_data.tar")
        # !!! current bug 5.08 need to change the save or remote path!!!
        #doc.create_openvpn_server_with_existing_data(docker_client,network_name,user_name,f"{subnet_first_part[0]}.{subnet_second_part[0]}.{subnet_base}.2",k, current_host,f"/home/{extracted_hosts_username[current_vm-1]}/ctf-data/{user_name}/Dockovpn_data/")
        # !!! Start the docker container. and push the old configs to the right place and then docker restart. 
        #doc.upload_existing_openvpn_config(docker_client,save_path,user_name)
        # 
        #click.echo(f"For {user_name } the OVPN Docker container is running and can be connected with the the existing data")

# !!! Start the docker container. and push the old configs to the right place and then docker restart. 
        #doc.upload_existing_openvpn_config(docker_client,save_path,user_name)
        # 
        #click.echo(f"For {user_name } the OVPN Docker container is running and can be connected with the the existing data")
      #
import docker 
import time

# Jump-host is currently not used
def create_jump_host(client, network_name, name, static_address,counter,host):
    """
    Create a jump host for secure access.

    Args:
        client (docker.DockerClient): An instance of the Docker client.
        network_name (str): The network to connect to.
        name (str): The name of the host (container).
        static_address (str): The static address of the host.
        counter (int): A counter to ensure unique port assignments.
        host (str): The host to create.

    Returns:
        docker.models.containers.Container: The container that was created.

    Raises:
        docker.errors.APIError: If an error occurred during the creation of the container.
    """
    endpoint_config = docker.types.EndpointConfig(
        version='1.44',
        ipv4_address=static_address
    )
    try:
        container = client.containers.run(
            image="binlab/bastion",
            detach=True,
            name=f"{name}_bastion",
            hostname="bastion",
            restart_policy={"Name": "always"},
            network=network_name,
            volumes={
                "/home/ubuntu/bastion/data/authorized_keys": {
                "bind": "/var/lib/bastion/authorized_keys",
                "mode": "ro"  # Read-only access
            },
            "/home/ubuntu/bastion/ssh": {  # Assuming you want to use a named volume (optional)
                "bind": "/usr/etc/ssh",
                "mode": "rw"  # Read-write access
            }
            },
            ports={"22/tcp": (22222+counter)},  # Map container port 22 to host port 22222
            environment={
                "PUBKEY_AUTHENTICATION": "true",  
                "GATEWAY_PORTS": "false",
                "PERMIT_TUNNEL": "false",
                "X11_FORWARDING": "false",
                "TCP_FORWARDING": "true",
                "AGENT_FORWARDING": "true",
                #"LISTEN_ADDRESS" : "0.0.0.0"
            },
            networking_config={
            network_name: endpoint_config}
        )
        return container 
    except docker.errors.APIError as e:
            print(f"Error creating container: {e}")
            raise      


def create_split_vpn_on_host(client, user_name, new_push_route, save_path,counter):
    """
    Create a split VPN for a specified user by modifying the server.conf and restarting the OpenVPN container.

    Args:
        client (docker.DockerClient): An instance of the Docker client.
        user_name (str): The name of the user for whom to create the split VPN.
        new_push_route (str): The new route to push to the client.
        save_path (str): The path to save and retrieve configuration files.

    Raises:
        docker.errors.NotFound: If the OpenVPN container for the user is not found.
    """
    container_name = f"{user_name}_openvpn"
    print(f"Creating Split VPN for {user_name}...")
    container = client.containers.get(container_name)
    try:
        local_save_path = f"{save_path}/data/{user_name}/server_conf"
        local_path_to_data = f"{save_path}/data/{user_name}/server_conf/server_conf_data.tar"
        os.makedirs(local_save_path, exist_ok=True)
        # !!! If you export this code snippet for the download to a function you get a very weird bug that the folder isnt existing etc.. So I left it this way
        archive, stat = container.get_archive("/opt/Dockovpn/config/server.conf")
        # Save the archive to a local file
        with open(local_path_to_data, "wb") as f:
            for chunk in archive:
                f.write(chunk)
        # Need to untar the data
        tar_func.untar_data(local_path_to_data,local_save_path)
        # Change server.conf
        local_path_to_conf_file =f"{save_path}/data/{user_name}/server_conf/server.conf"
        ovpn_func.modify_server_conf(local_path_to_conf_file,"#",new_push_route)
        # Tar the data
        tar_func.create_tar_archive(local_path_to_conf_file,local_path_to_data)
        # Upload 
        upload_tar_to_container(container,local_path_to_data,"/opt/Dockovpn/config/")
        # apk add tar
        exit_code, output = container.exec_run("apk add tar")
        # unpack tar file
        exit_code, output = container.exec_run("tar -xvf /opt/Dockovpn/config/server_conf_data.tar -f")
        # rm tar file 
        exit_code, output = container.exec_run("rm /opt/Dockovpn/config/server_conf_data.tar ")
        # restart docker
        container.restart(timeout=0)
        # Delay to give time to restart!
        time.sleep(2)
    except Exception as e:
        print(f"Error Creating split VPN: {e}")


def upload_existing_openvpn_config(client, save_path, user_name):
    try:
        print("Now uploading old openvpn configs!")
        container_name = f"{user_name}_openvpn"
        print(f"Creating Split VPN for {user_name}...")
        container = client.containers.get(container_name)
        exit_code, output = container.exec_run("rm -r /opt/Dockopvn_data")
        time.sleep(2)
        upload_tar_to_container(container,f"{save_path}/data/{user_name}/server_conf/server_conf_data.tar","/opt/Dockovpn/config/")
        upload_tar_to_container(container, f"{save_path}/data/{user_name}/dockovpn_data.tar","/opt/Dockovpn_data")

        exit_code, output = container.exec_run("rm -r clients/")
        exit_code, output = container.exec_run("rm -r pki/")
        exit_code, output = container.exec_run("rm ta.key")
        exit_code, output = container.exec_run("cp -r /opt/Dockovpn_data/Dockopn_data  /opt/Dockovpn_data/")
        time.sleep(1)
        exit_code, output = container.exec_run("rm -r /opt/Dockovpn_data/Dockopn_data/")
        # apk add tar
        # exit_code, output = container.exec_run("apk add tar")
        # unpack tar file
        #exit_code, output = container.exec_run("tar -xvf /opt/Dockovpn/config/server_conf_data.tar -f")
        # rm tar file 
       # exit_code, output = container.exec_run("rm /opt/Dockovpn/config/server_conf_data.tar ")
        # unpack tar file
        #exit_code, output = container.exec_run("tar -xvf /opt/dockovpn_data.tar -f")
        

        print("Upload of old configs to docker container is done")
        time.sleep(1)
        container.restart(timeout=0)
        # Delay to give time to restart!
        time.sleep(4)
    except docker.errors.NotFound:
        print(f"Error: Container {container_name} not found.")
        exit(1)
    except Exception as e:
        print(f"Error: Something is wrong with uploading the existing openvpn_config. {e}")
        exit(1)

def upload_tar_to_container(container, local_path_to_data, container_folder_path):
    """
    Uploads a tar archive to a specific folder within a Docker container.

    Args:
    client (docker.from_env): Docker client object.
    container_name (str): Name of the container.
    tar_file_path (str): Path to the tar archive on the host machine.
    container_folder_path (str): Path to the destination folder within the container.
    """
    try:
        # Open the tar file in read binary mode
        with open( local_path_to_data, "rb") as tar:
        # Upload the tar content as a stream
            container.put_archive(path=container_folder_path, data=tar)

        print(f"Tar archive uploaded to {container_folder_path} in container {container}")
    except docker.errors.APIError as e:
        print(f"Error uploading tar file: {e}")
    except FileNotFoundError:
        print(f"Error: File '{local_path_to_data}' not found.")


def send_tar_file_via_ssh(tar_file_path, host_username, remote_host, remote_path, remote_port=22):
    # Parse the user and host from the user_host variable
    
    # Create an SSH client
    ssh = paramiko.SSHClient()
    
    # Load SSH host keys
    ssh.load_system_host_keys()
    
    # Add missing host keys
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # Connect to the remote host using SSH agent for authentication
        ssh.connect(remote_host, port=remote_port, username=host_username)
        
        # Extract the remote directory path
        remote_dir = os.path.dirname(remote_path)
        
        # Ensure the remote directory exists
        stdin, stdout, stderr = ssh.exec_command(f'mkdir -p {remote_dir}')
        stdout.channel.recv_exit_status()  # Wait for the command to complete
        
        # Use SFTP to copy the file
        sftp = ssh.open_sftp()
        sftp.put(tar_file_path, remote_path)
        sftp.close()
        
        print(f"File {tar_file_path} successfully sent to {remote_host}:{remote_path}")
        
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Close the SSH connection
        ssh.close()


def send_and_extract_tar_via_ssh(tar_file_path, host_username, remote_host, remote_path, remote_port=22):
    # Create an SSH client
    ssh = paramiko.SSHClient()
    
    # Load SSH host keys
    ssh.load_system_host_keys()
    
    # Add missing host keys
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # Connect to the remote host using SSH agent for authentication
        ssh.connect(remote_host, port=remote_port, username=host_username)
        
        # Extract the remote directory path
        remote_dir = os.path.dirname(remote_path)
        
        # Ensure the remote directory exists
        stdin, stdout, stderr = ssh.exec_command(f'sudo mkdir -p {remote_dir}')
        stdout.channel.recv_exit_status()  # Wait for the command to complete
        
        # Use SFTP to copy the tar file
        sftp = ssh.open_sftp()
        sftp.put(tar_file_path, remote_path)
        sftp.close()
        
        print(f"File {tar_file_path} successfully sent to {remote_host}:{remote_path}")
        
        # Extract the tar file on the remote host
        extract_command = f'sudo tar -xf {remote_path} -C {remote_dir}'
        stdin, stdout, stderr = ssh.exec_command(extract_command)
        stdout.channel.recv_exit_status()  # Wait for the command to complete
        
        # Read the output and error streams
        output = stdout.read().decode()
        error = stderr.read().decode()
        
        # Print the output and error (if any)
        if output:
            print("Output:\n", output)
        if error:
            print("Error:\n", error)
        
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Close the SSH connection
        ssh.close()


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

    
# Currently not used function because of Python click
def read_yaml_data(file_path):
    """
    Reads configuration data from a YAML file and validates the required fields.

    Args:
        file_path (str): Path to the YAML file to read.

    Returns:
        tuple: A tuple containing the following:
            - containers (list): List of Docker containers to be started for each user.
            - users (list): List of users.
            - key (str): Path to the private SSH key for host login.
            - hosts (list): List of hosts where the Docker containers are running.
            - subnet_first_part (str): IP address, formatted as firstpart.xx.xx.xx/24.
            - subnet_second_part (str): IP address, formatted as xx.second_part.xx.xx/24.
            - subnet_third_part (str): IP address, formatted as xx.xx.third_part.xx/24.

    Raises:
        ValueError: If any of the required fields are missing in the YAML data.
    """
    with open(file_path, 'r') as file:
        data = yaml.safe_load(file)
    
    # Use the helper function to validate and extract data
    return read_data_from_yaml(data)



