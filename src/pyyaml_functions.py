"""
This module provides functionalities for the CTF-Creator,
including reading and validating configuration data from a YAML file,
and extracting relevant information for setting up Docker containers and network configurations.

The main functionalities include:

1. Validating required fields in the YAML configuration.
2. Extracting and returning relevant data for setting up Docker containers.
3. Extracting host parts and usernames from host strings.

Functions:
- read_data_from_yaml(data): Validates and extracts configuration data from a provided dictionary.
- extract_hosts(hosts): Extracts the host part from each string in a list of hosts.
- extract_host_usernames(hosts): Extracts the username part from each string in a list of hosts.
"""

import re


def read_data_from_yaml(data):
    """
    Validates and extracts configuration data from a provided dictionary.

    Args:
        data (dict): Configuration data.

    Returns:
        tuple: A tuple containing:
            - containers (list): List of Docker containers to be started for each user.
            - users (list): List of users.
            - key (str): Path to the private SSH key for host login.
            - hosts (list): List of hosts where the Docker containers are running.
            - subnet_first_part (str): IP address segment formatted as firstpart.xx.xx.xx/24.
            - subnet_second_part (str): IP address segment formatted as xx.second_part.xx.xx/24.
            - subnet_third_part (str): IP address segment formatted as xx.xx.third_part.xx/24.

    Raises:
        ValueError: If any required fields are missing, not lists, or contain invalid values.
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

    # Ensure each entry is a list
    for field_name, field_value in [('containers', containers),
                                    ('users', users),
                                    ('identityFile', key),
                                    ('hosts', hosts),
                                    ('subnet_first_part', subnet_first_part),
                                    ('subnet_second_part', subnet_second_part),
                                    ('subnet_third_part', subnet_third_part)]:
        if not isinstance(field_value, list):
            raise ValueError(f"Expected '{field_name}' to be a list")
    
    # Ensure lists are not empty
    if not containers:
        raise ValueError("Expected 'containers' to be a non-empty list")
    if not users:
        raise ValueError("Expected 'users' to be a non-empty list")
    if not hosts:
        raise ValueError("Expected 'hosts' to be a non-empty list")
    if not key:
        raise ValueError("Expected 'identityFile' to be a non-empty list")
    if not subnet_first_part:
        raise ValueError("Expected 'subnet_first_part' to be a non-empty list")
    if not subnet_second_part:
        raise ValueError("Expected 'subnet_second_part' to be a non-empty list")
    if not subnet_third_part:
        raise ValueError("Expected 'subnet_third_part' to be a non-empty list")

    # Ensure subnet fields contain exactly one value and convert to integer
    for subnet_field, subnet_value in [('subnet_first_part', subnet_first_part),
                                       ('subnet_second_part', subnet_second_part),
                                       ('subnet_third_part', subnet_third_part)]:
        if len(subnet_value) != 1:
            raise ValueError(f"Expected '{subnet_field}' to contain exactly one value")
        
        try:
            subnet_value[0] = int(subnet_value[0])
        except ValueError:
            raise ValueError(f"Expected '{subnet_field}' to contain an integer value")
        
     # Ensure lists are not empty
    if not containers:
        raise ValueError("Expected 'containers' to be a non-empty list")
    if not users:
        raise ValueError("Expected 'users' to be a non-empty list")
    if not hosts:
        raise ValueError("Expected 'hosts' to be a non-empty list")
    if not key:
        raise ValueError("Expected 'identityFile' to be a non-empty list")

       # Ensure each host follows the 'username@ip_address' format
    host_pattern = re.compile(r'^[\w._-]+@\d{1,3}(?:\.\d{1,3}){3}$')
    for host in hosts:
        if not host_pattern.match(host):
            raise ValueError(f"Expected 'hosts' entries to be in the format 'username@ip_address', but got '{host}'")

    # Convert singular values to lists if needed
    containers = containers if isinstance(containers, list) else [containers]
    users = users if isinstance(users, list) else [users]
    hosts = hosts if isinstance(hosts, list) else [hosts]

    # Extract the singular values
    subnet_first_part = subnet_first_part[0]
    subnet_second_part = subnet_second_part[0]
    subnet_third_part = subnet_third_part[0]
 
    return containers, users, key, hosts, subnet_first_part, subnet_second_part, subnet_third_part


def extract_hosts(hosts):
    """
    Extracts the host part from each string in a list of hosts.

    Args:
        hosts (list): List of host strings, each containing an '@' symbol.

    Returns:
        list: A list of extracted host parts.

    Raises:
        ValueError: If a string does not contain exactly one '@' symbol or is empty.
    """
    extracted_hosts = []
    for host in hosts:
        if not host:
            raise ValueError("Host string cannot be empty")
        
        parts = host.split('@')
        if len(parts) != 2:
            raise ValueError(f"Host string must contain exactly one '@' symbol, but got: '{host}'")
        
        extracted_hosts.append(parts[1])
    
    return extracted_hosts


def extract_host_usernames(hosts):
    """
    Extracts the username part from each string in a list of hosts.

    Args:
        hosts (list): List of host strings, each containing exactly one '@' symbol.

    Returns:
        list: A list of extracted username parts.

    Raises:
        ValueError: If a host string does not contain exactly one '@' symbol or is empty.
    """
    extracted_usernames = []
    for host in hosts:
        if not host:
            raise ValueError("Empty string provided in hosts list")
        
        parts = host.split('@')
        
        if len(parts) != 2:
            raise ValueError(f"Invalid host format: '{host}'")

        extracted_username = parts[0]
        extracted_usernames.append(extracted_username)

    return extracted_usernames


