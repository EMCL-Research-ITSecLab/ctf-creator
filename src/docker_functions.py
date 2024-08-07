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

def create_openvpn_server_with_existing_data(client, network_name, name, static_address, counter, host_address, remote_path_to_mount):
    """
    Create an OpenVPN server container with specific configurations.

    Args:
        client (docker.DockerClient): An instance of the Docker client.
        network_name (str): The name of the network to use.
        name (str): The base name of the container to create.
        static_address (str): The IPv4 address to use for the container.
        counter (int): A counter to ensure unique port assignments.
        host_address (str): The host address for the OpenVPN configuration.

        !!!!!!!

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
            },
            volumes = [f"{remote_path_to_mount}:/opt/Dockovpn_data"]
            
        )
        return container
    except docker.errors.APIError as e:
        print(f"Error creating container: {e}")
        raise

def download_tar_from_container():
    print("dummy")
    #!!! not done copy code part from create split vpn on host and use it there 
    #!!! and download in te create split vpn on host the config folder too!


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
    except docker.errors.NotFound:
        print(f"Error: Container {container_name} not found.")
        exit(1)
    except Exception as e:
        print(f"Error: Something is wrong with {container_name}. {e}")
        exit(1)

    try:
        print("Executing command in container...")
        exit_code, output = container.exec_run("./genclient.sh", detach=True)
        # Delay to give time to run the command in the container
        time.sleep(4)
        ovpn_func.curl_client_ovpn_file_version(container,host_address, user_name, counter,save_path)

    except Exception as e:
        print(f"Error: Unable to execute command in container. {e}")
        exit(1)
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
        tar_func.untar_data(local_path_to_data,local_save_path)
    except docker.errors.NotFound:
        print(f"Error: Container {container_name} not found.")
        exit(1)
    except Exception as e:
        print(f"Error: Something is wrong with the saving of the ovpn_data!. {e}")
        exit(1)


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