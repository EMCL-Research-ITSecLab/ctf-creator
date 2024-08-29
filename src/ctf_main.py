"""
This module provides the main functionality for the CTF-Creator tool.

To use this module, you need to provide a YAML configuration file with the following structure:

Arguments for the YAML file:
  - name: Name of the YAML configuration.
  - containers: Docker containers to be started for each user.
  - users: List of users to be managed.
  - identityFile: Path to the private SSH key for host login.
  - hosts: List of hosts where the Docker containers are running.
  - subnet_first_part: IP address, formatted as first_part.xx.xx.xx/24.
  - subnet_second_part: IP address, formatted as xx.second_part.xx.xx/24.
  - subnet_third_part: IP address, formatted as xx.xx.third_part.xx/24.

Functions:
  - main(): Main function of the CTF-Creator, which performs the following tasks:
    1. Connects using SSH keys specified in the YAML file.
    2. Cleans up existing Docker containers and networks on the specified hosts.
    3. Creates Docker networks and OpenVPN configurations for each user.
    4. Deploys Docker containers as specified in the YAML file.
    5. Handles the creation and modification of OpenVPN configuration files.

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
import ovpn_helper_functions as ovpn_func
import readme_functions as readme
import time
import hosts_functions as hosts_func
import validation_functions as valid
from docker.errors import NotFound, APIError

# Click for reading data from the terminal


@click.command()
@click.option(
    "--config",
    prompt="Please enter the path to your .yaml file",
    help="The path to the .yaml configuration file for the CTF-Creator.",
    callback=valid.validate_yaml_file,
)
@click.option(
    "--save_path",
    prompt="Please enter the path where you want to save the user data e.g. /home/nick/ctf-creator",
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
            click.echo("YAML file loaded successfully.")
            click.echo(f"Save path '{save_path}' is valid.")
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
            click.echo(f"Containers: {containers}")
            click.echo(f"Users: {users}")
            click.echo(f"Key: {key}")
            click.echo(f"Hosts: {hosts}")
            click.echo(
                f"IP-Address Subnet-base: {subnet_first_part}.{subnet_second_part}.{subnet_third_part}"
            )

        number_of_vm = len(hosts)
        count_users = len(users)
        number_users_per_vm = count_users // number_of_vm
        # If uneven you have rest users which get distributed uniformly
        number_rest_users = count_users % number_of_vm
        click.echo(f"Number of users: {count_users}")
        click.echo(f"Number of users per VM: {number_users_per_vm}")
        click.echo(
            f"Number of remaining users to be distributed uniformly: {number_rest_users}"
        )
        # Extract Host Ip-Address from yaml file
        extracted_hosts = yaml_func.extract_hosts(hosts)
        extracted_hosts_username = yaml_func.extract_host_usernames(hosts)
        try:
            hosts_func.check_host_reachability_with_ping(extracted_hosts)
        except Exception as e:
            click.echo(f"An error occurred: {e}")

        #
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
                    print(f"Error executing command: {command}")
                    break
        except Exception as e:
            raise RuntimeError(f"An unexpected error occurred: {e}")

        # Terminal knows now the SSH-key

        try:
            hosts_func.check_host_reachability_with_SSH(hosts)
        except Exception as e:
            click.echo(f"An error occurred: {e}")
        # Clean up first
        # Initialize Docker client using the SSH connection
        # Remove all containers from the hosts
        click.echo(
            "Start to clean up the Hosts. Deletes old Docker-containers and networks. It might take some time."
        )
        for host in hosts:
            try:
                docker_client = docker.DockerClient(base_url=f"ssh://{host}")
                docker_client.containers.prune()
                # Stop all containers and remove them.
                #!!! Bug if you want to remove a container which deletes itself or got forced deleted manually
                for item in docker_client.containers.list(ignore_removed=True):
                    try:
                        docker_client.containers.prune()
                        item.stop()
                        item.remove(force=True)
                    except NotFound:
                        print(
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
        click.echo("Clean up process on hosts finished!")

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
            click.echo(f"Created Subnet: {subnet}")
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
            # !!! here is the og line! doc.create_network(docker_client,network_name,subnet,gateway)
            # 1st use case
            # Create Open VPN Server if save data for user is not existing!
            local_save_path_to_user = f"{save_path}/data/{user_name}"
            if not os.path.exists(local_save_path_to_user):
                doc.create_network(docker_client, network_name, subnet, gateway)
                click.echo(
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
                click.echo(f"The config files will be saved here {save_path}")
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
                # Writes a readmefile which describes reachable docker containers
                readme.write_readme_for_ovpn_connection(
                    local_save_path_to_user,
                    f"{subnet_first_part}.{subnet_second_part}.{subnet_base}",
                    containers,
                )
            # Starts OpenVPN-Container with existing data in save_path
            else:
                # 2nd and 3rd use case
                click.echo(f"OpenVPN data exists for the user: {user_name}")
                click.echo(
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
                    print(
                        f"The remote host {existing_host_ip} in the already generated client.ovpn is existing. Everything is fine!"
                    )
                else:
                    # 4th use case changed remote host in yaml config
                    print(
                        f"The remote host {existing_host_ip} in the old client.ovpn is not existing anymore."
                    )
                    print(
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
                click.echo(
                    f"For {user_name } the OVPN Docker container is running and can be connected with the the existing data"
                )

            # Create a container for each container in the list of containers.
            for i, element in enumerate(containers):
                container_name = element.split(":")[0]
                doc.create_container(
                    docker_client,
                    network_name,
                    user_name + f"_{container_name}_" + f"{i}",
                    f"{element}",
                    f"{subnet_first_part}.{subnet_second_part}.{subnet_base}.{3+i}",
                )
        # Print all changed usernames
        if new_changed_ovpn_files_users:
            click.echo("The following users had their OVPN files changed:")
            for user in new_changed_ovpn_files_users:
                click.echo(user)
        print("Done.")
    except FileNotFoundError:
        click.echo("Error: The specified file was not found.")
    except yaml.YAMLError as exc:
        click.echo(f"Error parsing YAML file: {exc}")
    except ValueError as exc:
        click.echo(f"Error in YAML data: {exc}")
    except Exception as e:
        click.echo(f"An unexpected error occurred: {e}")


# main function for the main module
if __name__ == "__main__":
    main()
