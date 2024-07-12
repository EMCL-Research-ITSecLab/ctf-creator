"""
This module provides the main functionalities for the CTF-Creator,
including creating Docker containers and networks with specific configurations.

The main functionalities include:
1. Creating Docker containers with specific static addresses.
2. Setting up an OpenVPN server and generating OpenVPN configurations for users.
3. Creating a jump host for secure access.
4. Creating Docker networks with specific IPAM configurations.

Functions:
- create_container(client, network_name, name, image, static_address): Creates a Docker container with the given name and image.
- create_openvpn_server(client, network_name, name, static_address, counter, host_address): Creates an OpenVPN server container with specific configurations.
- create_openvpn_config(client, user_name): Generates an OpenVPN configuration for a specified user.
- create_jump_host(client, network_name, name, static_address, counter, host): Creates a jump host with specific settings.
- create_network(client, name, subnet_, gateway_): Creates a Docker network with IPAM configuration.
"""

#!!! Have to update the docstring comments!

import docker
import docker.errors
import docker.types
from docker.models.networks import Network
import subprocess
import os
import tarfile


def create_container(client,network_name, name, image,static_adress):
    """
    Create a Docker container with the given name and image.

    Args:
        client (docker.DockerClient): An instance of the Docker client.
        network_name (str): The name of the network to use.
        name (str): The name of the container to create (must be unique).
        image (str): The image to run as the container.
        static_address (str): The IPv4 address to use for the container.

    Returns:
        docker.models.containers.Container: The container that was created.

    Raises:
        docker.errors.APIError: If an error occurred during the creation of the container.
    """

    #client = docker.from_env()
    endpoint_config = docker.types.EndpointConfig(
    version='1.44',  
    ipv4_address=static_adress)
    try:   
        container = client.containers.run(
            image,
            detach=True,
            name=name,
            network=network_name,
            networking_config={
            network_name: endpoint_config}
            #ipv4_address= static_adress
        )
        return container 
    except docker.errors.APIError as e:
            print(f"Error creating container: {e}")
            raise           

def create_openvpn_server(client, network_name,name, static_adress,counter,host_adress):
    """
    Create an OpenVPN server container with specific configurations.

    Args:
        client (docker.DockerClient): An instance of the Docker client.
        network_name (str): The name of the network to use.
        name (str): The base name of the container to create.
        static_address (str): The IPv4 address to use for the container.
        counter (int): A counter to ensure unique port assignments.
        host_address (str): The host address for the OpenVPN configuration.

    Returns:
        docker.models.containers.Container: The container that was created.

    Raises:
        docker.errors.APIError: If an error occurred during the creation of the container.
    """
  
    endpoint_config = docker.types.EndpointConfig(
    version='1.44',  
    ipv4_address=static_adress)
    try:
        container = client.containers.run(
            image="alekslitvinenk/openvpn",
            detach=True,
            name=f"{name}_openvpn",
            network = network_name,
            restart_policy = {"Name":"always"},
            #remove=True,
            cap_add=["NET_ADMIN"],
            ports={
            '1194/udp': (1194+counter),
            '8080/tcp': (80+counter)
            },
            #'1194/udp': ('0.0.0.0', 1194),
            #'80/tcp': ('0.0.0.0', 8080+counter)
            # !!! Make the host adress dynamic!
            environment={
               "HOST_ADDR": f"{host_adress}", 
            },
            networking_config={
            network_name: endpoint_config}
            #ipv4_address= static_adress
        )
        return container 
    except docker.errors.APIError as e:
            print(f"Error creating container: {e}")
            raise    


# !!! Gehört fast schon in eine neue python lib 
def curl_client_ovpn_zip_version(container,host_address, user_name, counter,save_path, max_retries_counter = 0, max_retries=5):
    #implement click so the first part can be changed!
    save_directory = f"{save_path}/data/{user_name}"
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
        curl_client_ovpn_zip_version(container, host_address, user_name, counter, save_path, max_retries_counter)
      else:
        print(f"Download failed after {max_retries} retries. Exiting.")
        exit(1)

    except Exception as e:
      print(f"Error: An unexpected error occurred - {e}")
      if max_retries_counter < max_retries:
        print(f"Retrying download (attempt {max_retries_counter+1} of {max_retries})")
        max_retries_counter +=1
        curl_client_ovpn_zip_version(container, host_address, user_name, counter, save_path, max_retries_counter)
      else:
        print(f"Download failed after {max_retries} retries. Exiting.")
        exit(1)


def curl_client_ovpn_conf_version(host_address, user_name, counter,save_path):
    #implement click so the first part can be changed!
    save_directory = f"{save_path}/data/{user_name}"
    url = f"http://{host_address}:{80 + counter}"

    try:
        # Ensure the save directory exists; create it if not
        os.makedirs(save_directory, exist_ok=True)

        # Construct the command to download the file using curl
        command = f"curl -o {save_directory}/client.conf {url}"

        # Run the command using subprocess
        subprocess.run(command, shell=True, check=True)
        
        print(f"File downloaded successfully to {save_directory}/client.conf")
    
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to download file. Command returned non-zero exit status ({e.returncode})")
    
    except Exception as e:
        print(f"Error: An unexpected error occurred - {e}")

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

def create_tar_archive_old(source_path, archive_name, compression=None):
  """
  Creates a tar archive (TAR file) from a source directory or list of files,
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
      # Add files or directories to the archive
      if os.path.isdir(source_path):
        # Add an entire directory
        for root, dirs, files in os.walk(source_path):
          for file in files:
            file_path = os.path.join(root, file)
            tar.add(file_path, arcname=os.path.relpath(file_path, source_path))
      else:
        # Add individual files
        if isinstance(source_path, list):
          for file_path in source_path:
            tar.add(file_path)
        else:
          tar.add(source_path)

      print(f"Tar archive '{archive_name}' created successfully.")
  except Exception as e:
    print(f"Error creating tar archive: {e}")

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

### Da gibt es bestimmt irgendeine funktion um dateien mit python zu ändern.
### cd config und dann suche alle push route. lösche die zeile oder einfache adde # davor
## schreibe die richtige push route 
## speichere
## docker restart!
## Führe die funktion vor dem speichern der aus, aber nach dem erstellen des containers!
def create_split_vpn(client, user_name,new_push_route, save_path):
    # Download current server.conf
    container_name = f"{user_name}_openvpn"
    print(f"Creating Split VPN for {user_name}...")
    container = client.containers.get(container_name)
    try:
        local_save_path = f"{save_path}/data/{user_name}/server_conf"
        local_path_to_data =f"{save_path}/data/{user_name}/server_conf/server_conf_data.tar"
        os.makedirs(local_save_path, exist_ok=True)
        archive, stat = container.get_archive("/opt/Dockovpn/config/server.conf")
        # Save the archive to a local file
        with open(local_path_to_data, "wb") as f:
            for chunk in archive:
                f.write(chunk)
        # Need to untar the data
        untar_data(local_path_to_data,local_save_path)
        # Change server.conf
        local_path_to_conf_file =f"{save_path}/data/{user_name}/server_conf/server.conf"
        modify_server_conf(local_path_to_conf_file,"#",new_push_route)
        # Tar the data
        create_tar_archive(local_path_to_conf_file,local_path_to_data)
        # Upload 
        upload_tar_to_container(container,local_path_to_data,"/opt/Dockovpn/config/")
        # apk add tar
        exit_code, output = container.exec_run("apk add tar")
        # unpack tar file
        exit_code, output = container.exec_run("tar -xvf /opt/Dockovpn/config/server_conf_data.tar -f")
        # rm tar file 
        exit_code, output = container.exec_run("rm /opt/Dockovpn/config/server_conf_data.tar ", detach=True)
        #exit_code, output = container.exec_run("rm /opt/Dockovpn/config/server.conf", detach=True)
        # !!! Place the server.conf in the right place!
        #exit_code, output = container.exec_run(f"", detach=True)
        # restart docker
        # !!! Bug on the restart so it has todo with the split VPN!
        container.restart(timeout=0)
    except Exception as e:
        print(f"Error Creating split VPN: {e}")
    


def modify_server_conf_old(filename, comment_char="#", new_push_route="10.13.0.0 255.255.255.0"):
  """
  Modifies a file by commenting out existing "push route" lines and adding a new one.

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
      for line in content:
        if line.startswith("push"):
          modified_lines.append(f"{comment_char} {line}")
        else:
          modified_lines.append(line)
          # push "route 10.13.13.0 255.255.255.0"
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

###!!! change name of function so it indicsates that it saves everything too!
def create_openvpn_config(client, user_name, counter, host_address,save_path,new_push_route):
    """
    Generate a new OpenVPN configuration for the specified user.

    Args:
        client (docker.DockerClient): An instance of the Docker client.
        user_name (str): The name of the user for whom to create the configuration.
        counter (int): Counter value for constructing URLs or commands.
        host_address (str): Host address for downloading files or executing commands.

    Raises:
        docker.errors.NotFound: If the OpenVPN container for the user is not found.
    """
    container_name = f"{user_name}_openvpn"
    print(f"Creating OpenVPN configuration for {user_name}...")
    
    # Download the folder with data 
    try:
        # FYI: Docker SDK python Docu is very poorly documented 
        container = client.containers.get(container_name)
        local_save_path = f"{save_path}/data/{user_name}"
        local_path_to_data =f"{save_path}/data/{user_name}/dockovpn_data.tar"
        os.makedirs(local_save_path, exist_ok=True)
        archive, stat = container.get_archive("/opt/Dockovpn_data")
        # Save the archive to a local file
        with open(local_path_to_data, "wb") as f:
            for chunk in archive:
                f.write(chunk)
        print(f"Container found: {container_name}", "And the Dockovpn_data folder is saved on the host")
    except docker.errors.NotFound:
        print(f"Error: Container {container_name} not found.")
        exit(1)
    except Exception as e:
        print(f"Error: Something is wrong with the saving of the ovpn_data!. {e}")
        exit(1)

    try:
        print("Executing command in container...")
        exit_code, output = container.exec_run("./genclient.sh z", detach=True)
        #exit_code, output = container.restart()
        # Assuming ./genclient.sh z generates client.ovpn in the container
        # Replace this assumption with actual logic based on your setup
        
        # Example: curl client.ovpn file after generation
        # !!!Maybe try to curl it agian if it failes!
        # !!! Restart the config and curl
        curl_client_ovpn_zip_version(container,host_address, user_name, counter,save_path)

    except Exception as e:
        print(f"Error: Unable to execute command in container. {e}")
        exit(1)



#!!! dockerovp tar einspielen 


# Need to set up split VPN
# apk update && apk add nano
# cd config
# nano server conf 
# delte or # all push lines out 
# add push "route 10.13.13.0 255.255.255.0"
# control x, yes safe
# restart docker!


def create_jump_host(client, network_name, name, static_adress,counter,host):
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
    ipv4_address=static_adress)
    try:   
        container = client.containers.run(
            image="binlab/bastion",
            detach=True,
            name=f"{name}_bastion",
            hostname="bastion",
            restart_policy = {"Name":"always"},
            network=network_name,
            #extra_hosts = {'docker-host': f"{host.split('@')[1]}"},
            #!!! Needs authorized_keys in the libne before bind!
            # !!! but when the folder is not created in the VM1-4 
            # then it creates a folder with authorized_keys instead of file
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
                #"AUTHORIZED_KEYS" : "/home/ubuntu/bastion/data/authorized_keys",
                # "TRUSTED_USER_CA_KEYS" : "/home/ubuntu/bastion/data",
                "GATEWAY_PORTS": "false",
                "PERMIT_TUNNEL": "false",
                "X11_FORWARDING": "false",
                "TCP_FORWARDING": "true",
                "AGENT_FORWARDING": "true",
                #"LISTEN_ADDRESS" : "0.0.0.0"
            },
            networking_config={
            network_name: endpoint_config}
            #ipv4_address= static_adress
        )
        return container 
    except docker.errors.APIError as e:
            print(f"Error creating container: {e}")
            raise      

def create_network(client,name, subnet_, gateway_):
    """
    Create a Docker network with IPAM configuration.

    Args:
        client (docker.DockerClient): An initialized Docker client.
        name (str): The name of the network to create.
        subnet_ (str): The subnet to use for the network.
        gateway_ (str): The gateway to use for the network.

    Returns:
        docker.models.networks.Network: The network that was created.
    """
    ipam_pool = docker.types.IPAMPool(
        subnet=subnet_,
        gateway=gateway_
    )
    ipam_config = docker.types.IPAMConfig(
        pool_configs=[ipam_pool]
    )

    # Create the network with IPAM configuration
    return client.networks.create(name,driver="bridge",ipam=ipam_config,check_duplicate=True) 


