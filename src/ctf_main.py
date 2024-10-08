"""
This module provides the main functionality for the CTF-Creator tool.

To use this module, you need to provide a YAML configuration file with the following structure:

Arguments for the YAML file:
  - name: Name of the YAML configuration.
  - containers: Docker containers deployed for each user.
  - users: List of users to be managed.
  - identityFile: Path to the private SSH key for host login.
  - hosts: List of hosts where the Docker containers are running.
  - subnet_first_part: IP address, formatted as first_part.xx.xx.xx/24.
  - subnet_second_part: IP address, formatted as xx.second_part.xx.xx/24.
  - subnet_third_part: IP address, formatted as xx.xx.third_part.xx/24.

Functions:
  - main(): Main function of the CTF-Creator, which performs the following tasks:
    1. YAML Configuration Parsing
    2. SSH Connection Initialization
    3. Host Reachability and SSH Connectivity Check
    4. Cleanup of Existing Docker Containers and Networks
    5. Subnet Calculation and Network Setup
    6. OpenVPN Server Setup
    7. OpenVPN Configuration Management
    8. Docker Container Deployment
    9. Documentation and Output Generation
    10. Error Handling and logger

Args:
  - config: Path to the YAML configuration file.
  - save_path: Directory where user data will be saved.
"""

import docker_functions as doc
import docker
import pyyaml_functions as yaml_func
import yaml
import subprocess
from docker.errors import NotFound
import click
import os
import sys
import ovpn_helper_functions as ovpn_func
import readme_functions as readme
import time
import hosts_functions as hosts_func
import validation_functions as valid
from docker.errors import NotFound, APIError

sys.path.append(os.getcwd())
from src.log_config import get_logger

logger = get_logger("data_inspection.inspector")


# Click for reading data from the terminal
@click.command()
@click.option(
    "--config",
    required=True,
    help="The path to the .yaml configuration file for the CTF-Creator.",
    callback=valid.validate_yaml_file,
)
@click.option(
    "--save_path",
    required=True,
    help="The path where you want to save the user data for the CTF-Creator. E.g. /home/nick/ctf-creator",
    callback=valid.validate_save_path,
)
def main(config, save_path):
    """
    Main function of the CTF-Creator.

    This function performs the following tasks:
      1. Loads and parses the YAML configuration file.
      2. Connects to hosts using SSH keys specified in the YAML file.
      3. Cleans up existing Docker containers and networks on each host.
      4. Creates Docker networks and OpenVPN servers, and generates configuration files for each user.
      5. Deploys Docker containers as specified in the YAML file.
      6. Modifies OpenVPN configuration files to include split VPN settings and updates existing configurations if present.

    Args:
      - config (str): Path to the YAML configuration file.
      - save_path (str): Directory where user data will be saved.
    """

    try:
        with open(config, "r") as file:
            data = yaml.safe_load(file)
            logger.info("YAML file loaded successfully.")
            logger.info(f"Save path '{save_path}' is valid.")
            # Process the YAML data as needed for the CTF-Creator
            (
                containers,
                users,
                key,
                hosts,
                subnet_first_part,
                subnet_second_part,
                subnet_third_part,
            ) = yaml_func.read_data_from_yaml(data)
            logger.info(f"Containers: {containers}")
            logger.info(f"Users: {users}")
            logger.info(f"Key: {key}")
            logger.info(f"Hosts: {hosts}")
            logger.info(
                f"IP-Address Subnet-base: {subnet_first_part}.{subnet_second_part}.{subnet_third_part}"
            )

        number_of_vm = len(hosts)
        count_users = len(users)
        number_users_per_vm = count_users // number_of_vm
        # If uneven you have rest users which get distributed uniformly
        number_rest_users = count_users % number_of_vm
        logger.info(f"Number of users: {count_users}")
        logger.info(f"Number of users per VM: {number_users_per_vm}")
        logger.info(
            f"Number of remaining users to be distributed uniformly: {number_rest_users}"
        )
        # Extract Host Ip-Address from yaml file
        extracted_hosts = yaml_func.extract_hosts(hosts)
        try:
            hosts_func.check_host_reachability_with_ping(extracted_hosts)
        except Exception as e:
            logger.error(f"An error occurred: {e}")

        # TODO Add as argument
        # Define ssh-agent commands as a list
        commands = [
            f'eval "$(ssh-agent)" ',
            # f'ssh-add {key}'
        ]

        # Iterate over the keys and add an ssh-add command for each key
        for k in key:
            commands.append(f"ssh-add {k}")

        try:
            # Run all commands in the list of commands
            for command in commands:
                result = subprocess.run(command, shell=True, executable="/bin/bash")
                if result.returncode != 0:
                    logger.error(f"Error executing command: {command}")
                    break
        except Exception as e:
            raise RuntimeError(f"An unexpected error occurred: {e}")

        # Terminal knows now the SSH-key

        try:
            hosts_func.check_host_reachability_with_SSH(hosts)
        except Exception as e:
            logger.error(f"An error occurred: {e}")
        # Clean up first
        # Initialize Docker client using the SSH connection
        # Remove all containers from the hosts
        logger.info(
            "Start to clean up the Hosts. Deletes old Docker-containers and networks. It might take some time."
        )
        for host in hosts:
            try:
                docker_client = docker.DockerClient(base_url=f"ssh://{host}")
                docker_client.containers.prune()
                # Stop all containers and remove them.
                for item in docker_client.containers.list(ignore_removed=True):
                    try:
                        docker_client.containers.prune()
                        item.stop()
                        item.remove(force=True)
                    except NotFound:
                        logger.error(
                            f"Container {item.id} not found. It might have been removed already. But it is ok."
                        )
                # Delete all docker networks
                docker_client.networks.prune()
                # Clean-up existing data from the Host
                hosts_func.execute_ssh_command(
                    host, "sudo test -d ctf-data/ && sudo rm -r ctf-data/"
                )
            except APIError as api_err:
                raise RuntimeError(
                    f"An error occurred while fetching the Docker API version on host {host}. "
                    f"This may indicate that Docker is not installed, not running, or not properly configured on the host. "
                    f"Please verify the following: "
                    f"1. Docker is installed and running on the host by using the command: 'docker info'. "
                    f"2. The Docker daemon is configured to accept remote connections if you are accessing it remotely. "
                    f"3. Network connectivity to the Docker daemon is not blocked by a firewall or network policy. "
                    f"4. You can run Docker commands on the remote host without needing `sudo` privileges, or if `sudo` is required, ensure proper permissions are set. "
                    f"5. Check Docker's listening ports with commands such as 'sudo netstat -lntp | grep dockerd'. "
                    f"6. Check the CTF-creators README.md for more instructions. "
                    f"Original error: {api_err.explanation}"
                )
            except Exception as e:
                raise RuntimeError(
                    f"An unexpected error occurred while connecting to Docker on host {host}. "
                    f"This may indicate that Docker is not installed, not running, or not properly configured on the host. "
                    f"Please verify the following: "
                    f"1. Docker is installed and running on the host by using the command: 'docker info'. "
                    f"2. The Docker daemon is configured to accept remote connections if you are accessing it remotely. "
                    f"3. Network connectivity to the Docker daemon is not blocked by a firewall or network policy. "
                    f"4. You can run Docker commands on the remote host without needing `sudo` privileges, or if `sudo` is required, ensure proper permissions are set. "
                    f"5. Check Docker's listening ports with commands such as 'sudo netstat -lntp | grep dockerd'. "
                    f"6. Check the CTF-creators README.md for more instructions. "
                    f"Original error: {e}"
                )
        logger.info("Clean up process on hosts finished!")

        # Start after Clean up
        # Begin with the first Host in the list in the yaml.file
        current_vm = 1
        current_host = extracted_hosts[current_vm - 1]
        docker_client = docker.DockerClient(base_url=f"ssh://{hosts[current_vm-1]}")
        new_changed_ovpn_files_users = []
        for k in range(len(users)):
            user_name = f"user_{users[k]}"
            network_name = f"{user_name}_network"
            # This function is used to calculate the subnet base and second part of the subnet.
            # Makes sure that correct Subnet IP-addresses are created
            if (subnet_third_part + k) // 256 > 0:
                subnet_second_part += 1
                subnet_base = 0
                subnet_third_part = 0

            subnet_base = (subnet_third_part + (k % 256)) % 256
            # Variables for Split VPN
            new_push_route = f"{subnet_first_part}.{subnet_second_part}.{subnet_base}.0 255.255.255.0"
            subnet = f"{subnet_first_part}.{subnet_second_part}.{subnet_base}.0/24"
            logger.info(f"Created Subnet: {subnet}")
            gateway = f"{subnet_first_part}.{subnet_second_part}.{subnet_base}.1"

            # Move to the next VM and distribute users evenly
            if k >= (current_vm * number_users_per_vm) + min(
                current_vm, number_rest_users
            ):
                current_vm += 1
                docker_client = docker.DockerClient(
                    base_url=f"ssh://{hosts[current_vm-1]}"
                )
                current_host = extracted_hosts[current_vm - 1]
            # 1st use case
            # Create Open VPN Server if save data for user is not existing!
            local_save_path_to_user = f"{save_path}/data/{user_name}"
            if not os.path.exists(local_save_path_to_user):
                doc.create_network(docker_client, network_name, subnet, gateway)
                logger.info(
                    f"For the user: {user_name}, an OpenVPN configuration file will be generated!"
                )
                doc.create_openvpn_server(
                    docker_client,
                    network_name,
                    user_name,
                    f"{subnet_first_part}.{subnet_second_part}.{subnet_base}.2",
                    k,
                    current_host,
                )
                # Create Open VPN files
                logger.info(f"The config files will be saved here {save_path}")
                # Creates and downloads the Openvpn configs for the user
                doc.create_openvpn_config(
                    docker_client, user_name, k, current_host, save_path, new_push_route
                )
                # Modifies client.ovpn file to configure spilt VPN for the user.
                ovpn_func.modify_ovpn_file(
                    f"{save_path}/data/{user_name}/client.ovpn",
                    1194 + k,
                    new_push_route,
                )
            # Starts OpenVPN-Container with existing data in save_path
            else:
                # 2nd and 3rd use case
                logger.info(f"OpenVPN data exists for the user: {user_name}")
                logger.info(
                    f"Data for the user: {user_name} will NOT be changed. Starting OVPN Docker container with existing data"
                )
                existing_host_ip, existing_port_number, existing_subnet = (
                    hosts_func.extract_ovpn_info(
                        f"{save_path}/data/{user_name}/client.ovpn"
                    )
                )
                existing_host_username = yaml_func.find_host_username_by_ip(
                    hosts, existing_host_ip
                )
                if existing_host_username is None:
                    existing_host_username = yaml_func.find_host_username_by_ip(
                        hosts, current_host
                    )
                if existing_host_ip in extracted_hosts:
                    logger.info(
                        f"The remote host {existing_host_ip} in the already generated client.ovpn is existing. Everything is fine!"
                    )
                else:
                    # 4th use case changed remote host in yaml config
                    logger.info(
                        f"The remote host {existing_host_ip} in the old client.ovpn is not existing anymore."
                    )
                    logger.info(
                        f"The generated client.ovpn for {user_name} gets changed locally. Please inform {user_name} and give him the new client.ovpn"
                    )
                    # Existing host is not existing anymore so change it into the current on from the loop iteration
                    existing_host_ip = current_host
                    changed_ovpn_username = ovpn_func.modify_ovpn_file_change_host(
                        f"{save_path}/data/{user_name}/client.ovpn",
                        current_host,
                        existing_port_number,
                        user_name,
                    )
                    if changed_ovpn_username:
                        new_changed_ovpn_files_users.append(changed_ovpn_username)
                # Send existing openvpn_data to hosts
                hosts_func.send_and_extract_tar_via_ssh(
                    f"{save_path}/data/{user_name}/dockovpn_data.tar",
                    existing_host_username,
                    existing_host_ip,
                    f"/home/{existing_host_username}/ctf-data/{user_name}/dock_vpn_data.tar",
                )
                time.sleep(2)
                # Change docker_client to the host which is in the already existing client.ovpn
                docker_client = docker.DockerClient(
                    base_url=f"ssh://{existing_host_username}@{existing_host_ip}"
                )
                doc.create_network(
                    docker_client,
                    network_name,
                    f"{existing_subnet}.0/24",
                    f"{existing_subnet}.1",
                )
                time.sleep(1)
                # Creates Openvpn server with existing data
                doc.create_openvpn_server_with_existing_data(
                    docker_client,
                    network_name,
                    user_name,
                    f"{existing_subnet}.2",
                    existing_port_number,
                    existing_host_ip,
                    f"/home/{existing_host_username}/ctf-data/{user_name}/Dockovpn_data/",
                )
                logger.info(
                    f"For {user_name } the OVPN Docker container is running and can be connected with the the existing data"
                )
            # Writes a readme file which describes reachable docker containers
            readme.write_readme_for_ovpn_connection(
                local_save_path_to_user,
                f"{subnet_first_part}.{subnet_second_part}.{subnet_base}",
                containers,
            )
            # Create a container for each container in the list of containers.
            for i, element in enumerate(containers):
                if ":" in element:
                    container_name = element.split(":")[0]
                else:
                    container_name = element
                doc.create_container(
                    docker_client,
                    network_name,
                    user_name + f"_{container_name}_" + f"{i}",
                    f"{element}",
                    f"{subnet_first_part}.{subnet_second_part}.{subnet_base}.{3+i}",
                )
        # Print all changed usernames
        if new_changed_ovpn_files_users:
            logger.info("The following users had their OVPN files changed:")
            for user in new_changed_ovpn_files_users:
                logger.info(user)
        logger.info("Done.")
    except FileNotFoundError:
        logger.error("Error: The specified file was not found.")
    except yaml.YAMLError as exc:
        logger.error(f"Error parsing YAML file: {exc}")
    except ValueError as exc:
        logger.error(f"Error in YAML data: {exc}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")


# main function for the main module
if __name__ == "__main__":
    main()
