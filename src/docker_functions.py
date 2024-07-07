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
def curl_client_ovpn(host_address, user_name, counter,save_path):
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
    
    except Exception as e:
        print(f"Error: An unexpected error occurred - {e}")


### Da gibt es bestimmt irgendeine funktion um dateien mit python zu ändern.
### cd config und dann suche alle push route. lösche die zeile oder einfache adde # davor
## schreibe die richtige push route 
## speichere
## docker restart!
## Führe die funktion vor dem speichern der aus, aber nach dem erstellen des containers!
def create_split_vpn():
    print()

###!!! change name of function so it indicsates that it saves everything too!
def create_openvpn_config(client, user_name, counter, host_address,save_path):
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
        
        # Assuming ./genclient.sh z generates client.ovpn in the container
        # Replace this assumption with actual logic based on your setup
        
        # Example: curl client.ovpn file after generation
        curl_client_ovpn(host_address, user_name, counter,save_path)

    except Exception as e:
        print(f"Error: Unable to execute command in container. {e}")
        exit(1)





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


