"""
This module provides core functionalities for reading and validating configuration data
from a YAML file and extracting relevant information for setting up Docker containers and
network configurations in the CTF (Capture The Flag) environment.

Key Features:
1. Validation of YAML Configuration: Ensures that all required fields in the YAML configuration
   are present, properly formatted, and contain valid values.
2. Docker Setup Support: Extracts and returns necessary data to set up Docker containers for users
   based on the configuration.
3. Host String Manipulation: Extracts host information and user names from formatted host strings.

Functions:
- `read_data_from_yaml(data)`: Validates and extracts configuration data from a provided dictionary.
- `extract_hosts(hosts)`: Extracts the host IP addresses from each string in a list of hosts.
- `find_host_username_by_ip(hosts, existing_host_ip)`: Finds and returns the username associated with a
  given IP address from a list of host strings.
  
"""

import re
import docker_functions as doc_func


def read_data_from_yaml(data):
    """
    Validates and extracts configuration data from a provided dictionary.

    This function ensures that all required fields are present, correctly formatted,
    and contain valid values. It also converts specific subnet values to integers
    and validates that the hosts are in the correct format.

    Args:
        data (dict): Configuration data expected to contain the following keys:
            - "containers": List of Docker container names.
            - "users": List of user names.
            - "identityFile": Path to the private SSH key used for host login.
            - "hosts": List of host addresses where the Docker containers will run.
            - "subnet_first_part": The first part of the subnet IP address as a list containing one string.
            - "subnet_second_part": The second part of the subnet IP address as a list containing one string.
            - "subnet_third_part": The third part of the subnet IP address as a list containing one string.

    Returns:
        tuple: A tuple containing:
            - containers (list): List of Docker containers to be started for each user.
            - users (list): List of users.
            - key (list): List containing the path to the private SSH key for host login.
            - hosts (list): List of hosts where the Docker containers are running.
            - subnet_first_part (int): First part of the subnet IP address.
            - subnet_second_part (int): Second part of the subnet IP address.
            - subnet_third_part (int): Third part of the subnet IP address.

    Raises:
        ValueError: If any required fields are missing, not lists, contain invalid values,
                    or if host addresses do not match the 'username@ip_address' format.
    """
    required_fields = [
        "containers",
        "users",
        "identityFile",
        "hosts",
        "subnet_first_part",
        "subnet_second_part",
        "subnet_third_part",
    ]

    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing {field} field in YAML data")

    # Extract and return the relevant data
    containers = data.get("containers", [])
    users = data.get("users", [])
    key = data.get("identityFile", [])
    hosts = data.get("hosts", [])
    subnet_first_part = data.get("subnet_first_part", [])
    subnet_second_part = data.get("subnet_second_part", [])
    subnet_third_part = data.get("subnet_third_part", [])

    # Ensure each entry is a list
    for field_name, field_value in [
        ("containers", containers),
        ("users", users),
        ("identityFile", key),
        ("hosts", hosts),
        ("subnet_first_part", subnet_first_part),
        ("subnet_second_part", subnet_second_part),
        ("subnet_third_part", subnet_third_part),
    ]:
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
    for subnet_field, subnet_value in [
        ("subnet_first_part", subnet_first_part),
        ("subnet_second_part", subnet_second_part),
        ("subnet_third_part", subnet_third_part),
    ]:
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
    host_pattern = re.compile(r"^[\w._-]+@\d{1,3}(?:\.\d{1,3}){3}$")
    for host in hosts:
        if not host_pattern.match(host):
            raise ValueError(
                f"Expected 'hosts' entries to be in the format 'username@ip_address', but got '{host}'"
            )

    for container in containers:
        doc_func.check_image_existence(container)

    # Convert singular values to lists if needed
    containers = containers if isinstance(containers, list) else [containers]
    users = users if isinstance(users, list) else [users]
    hosts = hosts if isinstance(hosts, list) else [hosts]

    # Extract the singular values
    subnet_first_part = subnet_first_part[0]
    subnet_second_part = subnet_second_part[0]
    subnet_third_part = subnet_third_part[0]

    return (
        containers,
        users,
        key,
        hosts,
        subnet_first_part,
        subnet_second_part,
        subnet_third_part,
    )


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

        parts = host.split("@")
        if len(parts) != 2:
            raise ValueError(
                f"Host string must contain exactly one '@' symbol, but got: '{host}'"
            )

        extracted_hosts.append(parts[1])

    return extracted_hosts


def find_host_username_by_ip(hosts, existing_host_ip):
    """
    Finds the username associated with a given IP address from a list of host entries.

    Args:
        hosts (list): A list of host entries in the format 'username@ipaddress'.
        existing_host_ip (str): The IP address to find in the hosts list.

    Returns:
        str: The username associated with the given IP address, or None if not found.

    """
    for host in hosts:
        parts = host.split("@")
        if len(parts) != 2:
            raise ValueError(
                f"Host string must contain exactly one '@' symbol, but got: '{host}'"
            )
        username, ip_address = host.split("@")
        if ip_address == existing_host_ip:
            return username

    print(
        f"Warning: The IP address {existing_host_ip} in the client.ovpn is not defined in the YAML configuration for the CTF-Creator."
    )
    return None
