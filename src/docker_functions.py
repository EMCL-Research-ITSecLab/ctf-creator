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
- create_openvpn_config(client, user_name, counter, host_address, save_path, new_push_route): Generates an OpenVPN configuration for a specified user.
- create_jump_host(client, network_name, name, static_address, counter, host): Creates a jump host with specific settings.
- create_network(client, name, subnet_, gateway_): Creates a Docker network with IPAM configuration.
"""

import docker
import docker.errors
import docker.types
from docker.models.networks import Network
import os
import tar_functions as tar_func
import ovpn_helper_functions as ovpn_func
import time

def create_container(client, network_name, name, image, static_address):
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
    endpoint_config = docker.types.EndpointConfig(
        version='1.44',
        ipv4_address=static_address
    )
    try:
        container = client.containers.run(
            image,
            detach=True,
            name=name,
            network=network_name,
            networking_config={
            network_name: endpoint_config}
        )
        return container 
    except docker.errors.APIError as e:
            print(f"Error creating container: {e}")
            raise           

def create_openvpn_server(client, network_name, name, static_address, counter, host_address):
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
        ipv4_address=static_address
    )
    try:
        container = client.containers.run(
            image="alekslitvinenk/openvpn",
            detach=True,
            name=f"{name}_openvpn",
            network=network_name,
            restart_policy={"Name": "always"},
            cap_add=["NET_ADMIN"],
            ports={
                '1194/udp': (1194 + counter),
                '8080/tcp': (80 + counter)
            },
            environment={
                "HOST_ADDR": f"{host_address}",
            },
            networking_config={
                network_name: endpoint_config
            }
        )
        return container
    except docker.errors.APIError as e:
        print(f"Error creating container: {e}")
        raise

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

def create_split_vpn(client, user_name, new_push_route, save_path):
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
        time.sleep(1)
    except Exception as e:
        print(f"Error Creating split VPN: {e}")

def create_openvpn_config(client, user_name, counter, host_address, save_path, new_push_route):
    """
    Generate a new OpenVPN configuration for the specified user.

    Args:
        client (docker.DockerClient): An instance of the Docker client.
        user_name (str): The name of the user for whom to create the configuration.
        counter (int): Counter value for constructing URLs or commands.
        host_address (str): Host address for downloading files or executing commands.
        save_path (str): The path to save and retrieve configuration files.
        new_push_route (str): The new route to push to the client.

    Raises:
        docker.errors.NotFound: If the OpenVPN container for the user is not found.
    """
    container_name = f"{user_name}_openvpn"
    print(f"Creating OpenVPN configuration for {user_name}...")
    
    # Download the folder with data 
    try:
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
        # Delay to give time to run the command in the container
        time.sleep(2)
        ovpn_func.curl_client_ovpn_zip_version(container,host_address, user_name, counter,save_path)

    except Exception as e:
        print(f"Error: Unable to execute command in container. {e}")
        exit(1)


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

def create_network(client, name, subnet_, gateway_):
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