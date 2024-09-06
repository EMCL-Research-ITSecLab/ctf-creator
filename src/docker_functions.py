"""
This module provides functionalities for managing Docker containers and networks,
as well as setting up and configuring OpenVPN servers.

The primary functionalities include:
1. Creating Docker containers with specific static IP addresses.
2. Setting up and configuring OpenVPN servers.
3. Generating OpenVPN configuration files for users.
4. Creating Docker networks with IPAM configurations.
5. Checking the existence of Docker images locally or in a remote registry.

Functions:
- create_container(client, network_name, name, image, static_address): Creates a Docker container with a specified name, image, and static IP address.
- create_openvpn_server(client, network_name, name, static_address, counter, host_address): Creates an OpenVPN server container with specified configurations.
- create_openvpn_server_with_existing_data(client, network_name, name, static_address, port_number, host_address, remote_path_to_mount): Creates an OpenVPN server container using existing data with specified configurations.
- create_openvpn_config(client, user_name, counter, host_address, save_path, new_push_route): Generates an OpenVPN configuration for a specified user and saves it to a specified path.
- create_network(client, name, subnet_, gateway_): Creates a Docker network with a specified name, subnet, and gateway using IPAM configuration.
- check_image_existence(image_name): Checks if a Docker image exists locally or in a remote registry and attempts to pull it if not found locally.
"""

import docker
import docker.errors
import docker.types
from docker.models.networks import Network
import os
import ovpn_helper_functions as ovpn_func
import time
import docker


def create_container(client, network_name, name, image, static_address):
    """
    Create a Docker container with a specific name, image, and static IP address.

    Args:
        client (docker.DockerClient): An instance of the Docker client.
        network_name (str): The name of the network to connect the container to.
        name (str): The name of the container to create (must be unique).
        image (str): The Docker image to use for the container.
        static_address (str): The static IPv4 address to assign to the container.

    Returns:
        docker.models.containers.Container: The created Docker container.

    Raises:
        docker.errors.APIError: If an error occurs during the container creation process.
    """
    endpoint_config = docker.types.EndpointConfig(
        version="1.44", ipv4_address=static_address
    )
    try:
        container = client.containers.run(
            image,
            detach=True,
            name=name,
            network=network_name,
            networking_config={network_name: endpoint_config},
        )
        return container
    except docker.errors.APIError as e:
        print(f"Error creating container: {e}")
        raise


def create_openvpn_server(
    client, network_name, name, static_address, counter, host_address
):
    """
    Create an OpenVPN server container with specific configurations.

    Args:
        client (docker.DockerClient): An instance of the Docker client.
        network_name (str): The name of the network to connect the container to.
        name (str): The base name of the OpenVPN server container.
        static_address (str): The static IPv4 address to assign to the OpenVPN server.
        counter (int): Counter for port assignment to ensure uniqueness.
        host_address (str): The host address to be used in the OpenVPN configuration.

    Returns:
        docker.models.containers.Container: The created OpenVPN server container.

    Raises:
        docker.errors.APIError: If an error occurs during the container creation process.
    """
    endpoint_config = docker.types.EndpointConfig(
        version="1.44", ipv4_address=static_address
    )
    try:
        container = client.containers.run(
            image="alekslitvinenk/openvpn",
            detach=True,
            name=f"{name}_openvpn",
            network=network_name,
            restart_policy={"Name": "always"},
            cap_add=["NET_ADMIN"],
            ports={"1194/udp": (1194 + counter), "8080/tcp": (80 + counter)},
            environment={
                "HOST_ADDR": f"{host_address}",
            },
            networking_config={network_name: endpoint_config},
        )
        return container
    except docker.errors.APIError as e:
        print(f"Error creating container: {e}")
        raise


def create_openvpn_server_with_existing_data(
    client,
    network_name,
    name,
    static_address,
    port_number,
    host_address,
    remote_path_to_mount,
):
    """
    Create an OpenVPN server container with existing data mounted.

    Args:
        client (docker.DockerClient): An instance of the Docker client.
        network_name (str): The name of the network to connect the container to.
        name (str): The base name of the OpenVPN server container.
        static_address (str): The static IPv4 address to assign to the OpenVPN server.
        counter (int): Counter for port assignment to ensure uniqueness.
        host_address (str): The host address to be used in the OpenVPN configuration.
        remote_path_to_mount (str): The path to the directory on the host to mount into the container.

    Returns:
        docker.models.containers.Container: The created OpenVPN server container with existing data mounted.

    Raises:
        docker.errors.APIError: If an error occurs during the container creation process.
    """

    endpoint_config = docker.types.EndpointConfig(
        version="1.44", ipv4_address=static_address
    )
    try:
        container = client.containers.run(
            image="alekslitvinenk/openvpn",
            detach=True,
            name=f"{name}_openvpn",
            network=network_name,
            restart_policy={"Name": "always"},
            cap_add=["NET_ADMIN"],
            ports={"1194/udp": (port_number), "8080/tcp": (port_number)},
            environment={
                "HOST_ADDR": f"{host_address}",
            },
            networking_config={network_name: endpoint_config},
            volumes=[f"{remote_path_to_mount}:/opt/Dockovpn_data"],
        )
        return container
    except docker.errors.APIError as e:
        print(f"Error creating container: {e}")
        raise


def create_openvpn_config(
    client, user_name, counter, host_address, save_path, new_push_route
):
    """
    Generate an OpenVPN configuration file for a specified user.

    Args:
        client (docker.DockerClient): An instance of the Docker client.
        user_name (str): The name of the user for whom to create the configuration.
        counter (int): Counter value for constructing URLs or commands.
        host_address (str): The address of the host for downloading files or executing commands.
        save_path (str): The path to save the OpenVPN configuration files.
        new_push_route (str): The new route to push to the OpenVPN client.

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
        time.sleep(5)
        ovpn_func.curl_client_ovpn_file_version(
            container, host_address, user_name, counter, save_path
        )

    except Exception as e:
        print(f"Error: Unable to execute command in container. {e}")
        exit(1)
    try:
        container = client.containers.get(container_name)
        local_save_path = f"{save_path}/data/{user_name}"
        local_path_to_data = f"{save_path}/data/{user_name}/dockovpn_data.tar"
        os.makedirs(local_save_path, exist_ok=True)
        archive, stat = container.get_archive("/opt/Dockovpn_data")
        # Save the archive to a local file
        with open(local_path_to_data, "wb") as f:
            for chunk in archive:
                f.write(chunk)
        print(
            f"Container found: {container_name}",
            "And the Dockovpn_data folder is saved on this system",
        )
    except docker.errors.NotFound:
        print(f"Error: Container {container_name} not found.")
        exit(1)
    except Exception as e:
        print(f"Error: Something is wrong with the saving of the ovpn_data!. {e}")
        exit(1)


def create_network(client, name, subnet_, gateway_):
    """
    Create a Docker network with specific IPAM configuration.

    Args:
        client (docker.DockerClient): An instance of the Docker client.
        name (str): The name of the network to create.
        subnet_ (str): The subnet to use for the network (e.g., '192.168.1.0/24').
        gateway_ (str): The gateway to use for the network (e.g., '192.168.1.1').

    Returns:
        docker.models.networks.Network: The created Docker network.

    Raises:
        docker.errors.APIError: If an error occurs during the network creation process.
    """
    ipam_pool = docker.types.IPAMPool(subnet=subnet_, gateway=gateway_)
    ipam_config = docker.types.IPAMConfig(pool_configs=[ipam_pool])

    # Create the network with IPAM configuration
    return client.networks.create(
        name, driver="bridge", ipam=ipam_config, check_duplicate=True
    )


def check_image_existence(image_name):
    """Checks if a Docker image exists in a remote registry using the Docker SDK for Python.
    Otherwise it checks if this image can be pulled.

    Args:
        image_name (str): The name of the image to check.

    Returns:
        bool: True if the image exists, False otherwise.

    Raises:
        docker.errors.ImageNotFound: If the image is not found in the remote registry.
    """

    try:
        local_client = docker.from_env()
        # Split image name into name and version if a colon is present

        # Attempt to inspect the image locally
        local_client.images.get(f"{image_name}")
        print(f"Image {image_name} exists locally.")
        return True
    except docker.errors.ImageNotFound:
        # If the image is not local, try to pull it
        try:
            print(f"Try to pull Image {image_name}. Could take some time.")
            local_client.images.pull(f"{image_name}")
            print(f"Image {image_name} pulled successfully.")
            return True
        except docker.errors.ImageNotFound:
            raise docker.errors.ImageNotFound(
                f"Error: Image {image_name} could not be pulled. Does this Docker Image exist?"
            )
