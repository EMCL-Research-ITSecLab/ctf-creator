"""
This module provides functionalities for the CTF-Creator,
including reading and validating configuration data from a YAML file,
and extracting relevant information for setting up Docker containers and network configurations.

The main functionalities include:

1. Validating required fields in the YAML configuration.
2. Extracting and returning relevant data for setting up Docker containers.
3. Reading a WireGuard configuration from a YAML file.
4. Extracting host information from provided data.

Functions:
- read_yaml_data(file_path): Reads and validates configuration data from a YAML file.
- extract_hosts(hosts): Extracts the host part from each string in a list of hosts.
"""
import yaml


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
            - wireguard_config (str): Name of the WireGuard configuration.
            - subnet_first_part (str): IP address, formatted as firstpart.xx.xx.xx/24.
            - subnet_second_part (str): IP address, formatted as xx.second_part.xx.xx/24.
            - subnet_third_part (str): IP address, formatted as xx.xx.third_part.xx/24.

    Raises:
        ValueError: If any of the required fields are missing in the YAML data.
    """
    with open(file_path, 'r') as file:
        data = yaml.safe_load(file)
    
    # Ensure containers field is stored in a list
    # Raise ValueError if containers field is missing in YAML data
    if 'containers' not in data:
        raise ValueError("Missing 'containers' field in YAML data")
    #if not isinstance(data['containers'], list):
        #raise ValueError("'containers' field must be a list")
    
    # Ensure users field is stored in a list
    # ValueError if users field is not in YAML data
    if 'users' not in data:
        raise ValueError("Missing 'users' field in YAML data")
    #if not isinstance(data['users'], list):
        #raise ValueError("'users' field must be a list")
    # Ensure Place_of_ssh_key field is stored in a list
    # ValueError if identityFile is not in YAML data
    if 'identityFile' not in data:
        raise ValueError("Missing 'identityFile' field in YAML data")
    
    # ValueError if hosts field is not in YAML data
    if 'hosts' not in data:
        raise ValueError("Missing 'hosts' field in YAML data")
    
    # Raised if the wireguard_config field is not in YAML data.
    if 'wireguard_config' not in data:
        raise ValueError("Missing 'wireguard_config' field in YAML data")
    
    #if 'subnet_begin' not in data:
    #    raise ValueError("Missing 'subnet_begin' field in YAML data")
    
    # ValueError if subnet_first_part is not in YAML data
    if 'subnet_first_part' not in data:
         raise ValueError("Missing 'subnet_first_part' field in YAML data")
    
    # ValueError if subnet_second_part is not in YAML data
    if 'subnet_second_part' not in data:
         raise ValueError("Missing 'subnet_second_part' field in YAML data")
    
    # ValueError if subnet_third_part is not in YAML data
    if 'subnet_third_part' not in data:
         raise ValueError("Missing 'subnet_third_part' field in YAML data")
    
    # Store containers and users in separate lists
    containers = data.get('containers', [])
    users = data.get('users', [])
    key = data.get('identityFile', [])
    hosts = data.get('hosts' ,[])
    wireguard_config = data.get('wireguard_config' ,[])
    #subnet_begin = data.get('subnet_begin' ,[])
    subnet_first_part = data.get('subnet_first_part' ,[])
    subnet_second_part = data.get('subnet_second_part' ,[])
    subnet_third_part = data.get('subnet_third_part' ,[])
  
    
    return containers, users, key, hosts, wireguard_config,subnet_first_part, subnet_second_part, subnet_third_part


# Function to extract the host part from each string
def extract_hosts(hosts):
    """
    Extracts the host part from each string in a list of hosts.

    Args:
        hosts (list): List of host strings, each containing an '@' symbol.

    Returns:
        list: A list of extracted host parts. If a host string does not contain an '@' symbol, None is returned for that entry.
    """
    extracted_hosts = []
    for host in hosts:
        try:
            extracted_host = host.split('@')[1]
            extracted_hosts.append(extracted_host)
        except IndexError:
            # Handle the case where there is no '@' symbol in the string
            extracted_hosts.append(None)
    return extracted_hosts