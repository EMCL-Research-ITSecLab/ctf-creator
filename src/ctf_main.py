"""
This module provides the main function of the CTF-Creator.
To use this module, you need to provide a YAML configuration file.

Arguments for the YAML file:
  - name: Name of the YAML configuration.
  - containers: Docker containers that get started for each user.
  - users: List of users.
  - identityFile: Path to the private SSH key for host login.
  - hosts: Hosts where the Docker containers are running.
  - subnet_first_part: IP address, formatted as first_part.xx.xx.xx/24.
  - subnet_second_part: IP address, formatted as xx.second_part.xx.xx/24.
  - subnet_third_part: IP address, formatted as xx.xx.third_part.xx/24.

Functions:
  - main(): Main function of the CTF-Creator

Args: 
  - config: yaml file which is specified above
  - save_path: Path where the user date gets saved
"""
# !!! Second use case permisson error bug
# Imports
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

# Click for reading data from the terminal 
@click.command()
@click.option('--config', prompt='Please enter the path to your .yaml file', help='The path to the .yaml configuration file for the CTF-Creator.')
@click.option('--save_path', prompt="Please enter the path where you want to save the user data e.g. /home/nick/ctf-creator", help="The path where you want to save the user data for the CTF-Creator. E.g. /home/nick/ctf-creator")
def main(config, save_path):
  """
  Main function of the CTF-Creator.

  Functionalities:
    1. Connects using a WireGuard connection defined in the YAML file.
    2. Cleans up all existing networks and running containers.
    3. Creates a network for each user.
    4. Creates an OpenVPN server and an ovpn.config for each user.
    5. Creates all Docker containers defined in the YAML file for each user.

  Args:
    - config: Path to Yaml configuration file 
    - save_path: Save path for the user data
  """

  try:
    with open(config, 'r') as file:
      data = yaml.safe_load(file)
      click.echo('YAML file loaded successfully.')
    # Process the YAML data as needed for the CTF-Creator
      containers,users,key,hosts,subnet_first_part,subnet_second_part,subnet_third_part  = yaml_func.read_data_from_yaml(data)
      click.echo(f"Containers: {containers}")
      click.echo(f"Users: {users}")
      click.echo(f"Key: {key}")
      click.echo(f"Hosts: {hosts}")
      click.echo(f"IP-Address Subnet-base: {subnet_first_part[0]}.{subnet_second_part[0]}.{subnet_third_part[0]}")
   
    
    number_of_vm = len(hosts)
    count_users = len(users)
    number_users_per_vm = count_users // number_of_vm
    # If uneven you have rest users which get distributed uniformly 
    number_rest_users =  count_users % number_of_vm
    click.echo(f"Number of users: {count_users}")
    click.echo(f"Number of users per VM: {number_users_per_vm}")
    click.echo(f"Number of remaining users to be distributed uniformly: {number_rest_users}")
    # Extract Host Ip-Address from yaml file
    extracted_hosts = yaml_func.extract_hosts(hosts)
    extracted_hosts_username=yaml_func.extract_host_usernames(hosts)

    hosts_func.check_host_reachability_with_ping(extracted_hosts)

    # Define ssh-agent commands as a list
    commands = [
      f'eval "$(ssh-agent)" ',
      f'ssh-add {key[0]}'
    ]
  
   
    # Run all commands in the list of commands
    for command in commands:
        result = subprocess.run(command, shell=True, executable="/bin/bash")
        if result.returncode != 0:
            print(f"Error executing command: {command}")
            break

    # Terminal knows now the SSH-key

    hosts_func.check_host_reachability_with_SSH(hosts)
    
    # Clean up first
    # Initialize Docker client using the SSH connection
    # Remove all containers from the hosts
    click.echo("Start to clean up the Hosts. Deletes old Docker-containers and networks")
    #!!! Does not give an error warning if the ssh connection fails due to not being in the rigt wireguard vpn
    for host in hosts:
      docker_client =  docker.DockerClient(base_url=f"ssh://{host}")
      docker_client.containers.prune()
      # Stop all containers and remove them.
      #!!! Bug if you want to remove a container which deletes itself or got forced deleted manually
      for item in docker_client.containers.list(ignore_removed=True):
        try:
          docker_client.containers.prune()
          item.stop()
          item.remove(force=True)
        except NotFound:
          print(f"Container {item.id} not found. It might have been removed already. But it is ok.")
      # Delete all docker networks
      docker_client.networks.prune()
      # !!! do only the cleanup if the files exists or just write it is not bad or something
      hosts_func.execute_ssh_command(host,f"sudo rm -r ctf-data" )
    click.echo("Clean up process on hosts finished!")
    
    # Start after Clean up
    # Begin with the first Host in the list in the yaml.file
    current_vm = 1
    current_host = extracted_hosts[current_vm-1]
    docker_client =  docker.DockerClient(base_url=f"ssh://{hosts[current_vm-1]}")
    for k in range (len(users)): #len(users)
      user_name = f"user_{users[k]}"
      network_name = f"{user_name}_network"
      # This function is used to calculate the subnet base and second part of the subnet.
      # Makes sure that correct Subnet IP-addresses are created
      if ((subnet_third_part[0] + k) // 256 > 0):
        subnet_second_part[0] += 1
        subnet_base =0
        subnet_third_part[0] = 0 
      
      subnet_base = (subnet_third_part[0]+ (k%256)) % 256
      # Calculation for Split VPN
      new_push_route = f"{subnet_first_part[0]}.{subnet_second_part[0]}.{subnet_base}.0 255.255.255.0"
      subnet = f"{subnet_first_part[0]}.{subnet_second_part[0]}.{subnet_base}.0/24"
      click.echo(f"Created Subnet: {subnet}")
      gateway = f"{subnet_first_part[0]}.{subnet_second_part[0]}.{subnet_base}.1"

      # Move to the next VM and distribute users evenly
      if k >= (current_vm * number_users_per_vm) + min(current_vm, number_rest_users):
        current_vm +=1
        docker_client =  docker.DockerClient(base_url=f"ssh://{hosts[current_vm-1]}")
        current_host = extracted_hosts[current_vm-1]
      doc.create_network(docker_client,network_name,subnet,gateway)

      # Example to create a Jump Host but it it currently not used!
      #doc.create_jump_host(docker_client,network_name,user_name,f"{subnet_first_part[0]}.{subnet_second_part[0]}.{subnet_base}.2",k,hosts[current_vm-1])
      
      # Create Open VPN Server if save data for user is not existing!
      local_save_path_to_user = f"{save_path}/data/{user_name}"
      if not os.path.exists(local_save_path_to_user):
        click.echo(f"For the user: {user_name}, an OpenVPN configuration file will be generated!")
        doc.create_openvpn_server(docker_client,network_name,user_name,f"{subnet_first_part[0]}.{subnet_second_part[0]}.{subnet_base}.2",k, current_host)
        # Create Open VPN files
        click.echo(f"The config files will be saved here {save_path}")
        #!!! Bug in create split VPN test it does not chang the other server conf it a different folder!
        #doc.create_split_vpn_on_host(docker_client,user_name,new_push_route,save_path,k)
        doc.create_openvpn_config(docker_client,user_name,k,current_host,save_path, new_push_route)
        # Modifies client.ovpn file to configure spilt VPN for the user.
        ovpn_func.modify_ovpn_file(f"{save_path}/data/{user_name}/client.ovpn",1194+k,new_push_route)
        readme.write_readme_for_ovpn_connection(local_save_path_to_user,f"{subnet_first_part[0]}.{subnet_second_part[0]}.{subnet_base}",containers)
      else:
        click.echo(f"OpenVPN data exists for the user: {user_name}")
        click.echo(f"Data for the user: {user_name} will NOT be changed. Starting OVPN Docker container with existing data")
        #!!! To mount the data correctly need to send the data to the host!!! make sure it funtionkioert bugfree
        #!!! better send a python script per ssh and start it?!
        #!!! change the mount folder in start ovpn with old data!
        #hosts_func.execute_ssh_command(hosts[current_vm-1],"mkdir download_dockovpn_data")
        #hosts_func.send_tar_file_via_ssh(f"{save_path}/data/{user_name}/dockovpn_data.tar",hosts[current_vm-1],"/home/ubuntu/download_dockovpn_data/dockovpn_data.tar")
        #hosts_func.execute_ssh_command(hosts[current_vm-1],"tar -xvf /home/ubuntu/download_dockovpn_data/dockovpn_data.tar -f")
        #hosts_func.execute_ssh_command(hosts[current_vm-1],f"sudo rm -r ctf-data" )
        hosts_func.send_and_extract_tar_via_ssh_v2(f"{save_path}/data/{user_name}/dockovpn_data.tar",extracted_hosts_username[current_vm-1],extracted_hosts[current_vm-1],f"/home/{extracted_hosts_username[current_vm-1]}/ctf-data/{user_name}/dock_vpn_data.tar")
        # !!! current bug 5.08 need to change the save or remote path!!!
        doc.create_openvpn_server_with_existing_data(docker_client,network_name,user_name,f"{subnet_first_part[0]}.{subnet_second_part[0]}.{subnet_base}.2",k, current_host,f"/home/{extracted_hosts_username[current_vm-1]}/ctf-data/{user_name}/Dockovpn_data/")
        # !!! Start the docker container. and push the old configs to the right place and then docker restart. 
        #doc.upload_existing_openvpn_config(docker_client,save_path,user_name)
        # 
        click.echo(f"For {user_name } the OVPN Docker container is running and can be connected with the the existing data")
      #
      # Create a container for each container in the list of containers.
      for i, element in enumerate(containers):
        container_name = element.split(':')[0]
        doc.create_container(docker_client,network_name,user_name + f"_{container_name}_" + f"{i}", f"{element}", f"{subnet_first_part[0]}.{subnet_second_part[0]}.{subnet_base}.{3+i}")
    print("Done.")
  except FileNotFoundError:
    click.echo('Error: The specified file was not found.')
  except yaml.YAMLError as exc:
    click.echo(f'Error parsing YAML file: {exc}')
  except ValueError as exc:
    click.echo(f'Error in YAML data: {exc}')
  except Exception as e:
    click.echo(f'An unexpected error occurred: {e}')

# main function for the main module
if __name__ == "__main__":
    main()



