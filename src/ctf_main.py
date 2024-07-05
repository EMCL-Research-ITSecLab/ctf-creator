# Curl etc does work now. there was a very nasty bug using python request bib so I had to change everything!
# Have to implement split VPN and click
# New Version very soon!
"""
This module provides the main function of the CTF-Creator.
To use this module, you have to provide a YAML config file.
Arguments for the YAML file:
  - name: Name of the YAML config.
  - containers: Docker containers that get started for each user.
  - users: List of users.
  - identityFile: Path to the private SSH key for host login.
  - hosts: Hosts where the Docker containers are running.
  - subnet_first_part: IP address, formatted as firstpart.xx.xx.xx/24.
  - subnet_second_part: IP address, formatted as xx.second_part.xx.xx/24.
  - subnet_third_part: IP address, formatted as xx.xx.third_part.xx/24.
  - wireguard_config: Name of your WireGuard config needed to connect to the hosts.
Functions:
  - main(): Main function of the CTF-Creator
"""


import docker_functions as doc 
import ssh_functions as ssh
import zip_functions as zip
import docker
import os
import pyyaml_functions as yaml
import subprocess
from docker.errors import NotFound


#!!! install click
## Click creator übergeb die config yaml!
containers,users,key,hosts,wireguard_config,subnet_first_part,subnet_second_part,subnet_third_part  = yaml.read_yaml_data("test.yaml")
number_of_vm = len(hosts)
count_users = len(users)
number_users_per_vm = count_users // number_of_vm
# If uneven you have rest users which get distributed uniformly 
number_rest_users =  count_users % number_of_vm
print("count_users = ",count_users)
print("number_users_per_vm = ", number_users_per_vm)
print("number_rest_users = ", number_rest_users)
extracted_hosts = yaml.extract_hosts(hosts)

def main():
  """
  Main function of the CTF-Creator.

  Functionalities:
    1. Connects using a WireGuard connection defined in the YAML file.
    2. Cleans up all existing networks and running containers.
    3. Creates a network for each user.
    4. Creates an OpenVPN server and an ovpn.config for each user.
    5. Creates all Docker containers defined in the YAML file for each user.

  Args:
    - tbd
  """

  # Define ssh-agent commands as a list
  commands = [
    f'sudo wg-quick up {wireguard_config[0]}',
    'eval `ssh-agent`',
    f'ssh-add {key[0]}'
  ]

  # Run all commands in the list of commands
  for command in commands:
    subprocess.run(command, shell=True)

  # Terminal knows now the SSH-key
  
  # Clean up first
  # Initialize Docker client using the SSH connection
  # Remove all containers from the hosts
  for host in hosts:
    docker_client =  docker.DockerClient(base_url=f"ssh://{host}")
    docker_client.containers.prune()
    # Stop all containers and remove them.
    #!!! Bug if you want to remove a container which deletes itself or get foreced deleted
    for item in docker_client.containers.list(ignore_removed=True):
      try:
        docker_client.containers.prune()
        item.stop()
        item.remove(force=True)
      except NotFound:
        print(f"Container {item.id} not found. It might have been removed already. But it is ok.")
    # Delte all docker networks
    docker_client.networks.prune()


  # Start from the first VM
  current_vm = 1
  current_host = extracted_hosts[current_vm-1]
  docker_client =  docker.DockerClient(base_url=f"ssh://{hosts[current_vm-1]}")
  for k in range (len(users)): #len(users)
    user_name = f"user_{users[k]}"
    network_name = f"{user_name}_network"
    # This function is used to calculate the subnet base and second part of the subnet.
    if ((subnet_third_part[0] + k) // 256 > 0):
      subnet_second_part[0] += 1
      subnet_base =0
      subnet_third_part[0] = 0 
    # !!! Small Bug subnetbase does not start from 0!
    subnet_base = (subnet_third_part[0]+ (k%256)) % 256
   
    subnet = f"{subnet_first_part[0]}.{subnet_second_part[0]}.{subnet_base}.0/24"
    print("subnet", subnet)
    
    gateway = f"{subnet_first_part[0]}.{subnet_second_part[0]}.{subnet_base}.1"

    # Move to the next VM and distribute users evenly
    if k >= (current_vm * number_users_per_vm) + min(current_vm, number_rest_users):
      current_vm +=1
      docker_client =  docker.DockerClient(base_url=f"ssh://{hosts[current_vm-1]}")
      current_host = extracted_hosts[current_vm-1]
    doc.create_network(docker_client,network_name,subnet,gateway)

    # Create Jump Host
    #doc.create_jump_host(docker_client,network_name,user_name,f"{subnet_first_part[0]}.{subnet_second_part[0]}.{subnet_base}.2",k,hosts[current_vm-1])
    
    # Create Open VPN Server
    doc.create_openvpn_server(docker_client,network_name,user_name,f"{subnet_first_part[0]}.{subnet_second_part[0]}.{subnet_base}.2",k, current_host)
    # Create Open VPN files
    doc.create_openvpn_config(docker_client,user_name,k,current_host)

    # !!!  Save the OVPN Server config in these special ordner in the docker container
    # !!! send it to the pc starting the skript
    # !!! Save the ctf-creator/data as zip
    # Create other containers in the same network
    # Create a container for each container in the list of containers.
    for i, element in enumerate(containers):
      container_name = element.split(':')[0]
      doc.create_container(docker_client,network_name,user_name + f"_{container_name}_" + f"{i}", f"{element}", f"{subnet_first_part[0]}.{subnet_second_part[0]}.{subnet_base}.{3+i}")
      
  print("Done.")
    

# main function for the main module
if __name__ == "__main__":
    main()



