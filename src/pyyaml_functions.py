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

def read_data_from_yaml(data):
    """
    Validates and extracts configuration data from a provided dictionary.

    Args:
        data (dict): Configuration data.

    Returns:
        tuple: A tuple containing the following:
            - containers (list): List of Docker containers to be started for each user.
            - users (list): List of users.
            - key (str): Path to the private SSH key for host login.
            - hosts (list): List of hosts where the Docker containers are running.
            - subnet_first_part (str): IP address, formatted as firstpart.xx.xx.xx/24.
            - subnet_second_part (str): IP address, formatted as xx.second_part.xx.xx/24.
            - subnet_third_part (str): IP address, formatted as xx.xx.third_part.xx/24.

    Raises:
        ValueError: If any of the required fields are missing in the YAML data.
    """
    required_fields = ['containers', 'users', 'identityFile', 'hosts', 
                       'subnet_first_part', 'subnet_second_part', 'subnet_third_part']
    
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing {field} field in YAML data")

    # Extract and return the relevant data
    containers = data.get('containers', [])
    users = data.get('users', [])
    key = data.get('identityFile', [])
    hosts = data.get('hosts', [])
    subnet_first_part = data.get('subnet_first_part', [])
    subnet_second_part = data.get('subnet_second_part', [])
    subnet_third_part = data.get('subnet_third_part', [])
    
    return containers, users, key, hosts, subnet_first_part, subnet_second_part, subnet_third_part

# Currently not used function because of Python click
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
            - subnet_first_part (str): IP address, formatted as firstpart.xx.xx.xx/24.
            - subnet_second_part (str): IP address, formatted as xx.second_part.xx.xx/24.
            - subnet_third_part (str): IP address, formatted as xx.xx.third_part.xx/24.

    Raises:
        ValueError: If any of the required fields are missing in the YAML data.
    """
    with open(file_path, 'r') as file:
        data = yaml.safe_load(file)
    
    # Use the helper function to validate and extract data
    return read_data_from_yaml(data)

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
