"""
This module provides functionality to generate a README.md file with instructions for connecting to a subnet using OpenVPN.

The main functionality includes:

1. Creating a README.md file with instructions on how to connect to a specified subnet.
2. Listing reachable Docker container IP addresses based on the number of containers.

Functions:
- write_readme_for_ovpn_connection(location, subnet, containers): Writes a README.md file to the specified location with details about connecting to the subnet and reachable container IP addresses.
"""
import os


def write_readme_for_ovpn_connection(location, subnet, containers):
    """
    Writes a README.md file to the specified location with details about connecting to the subnet and reachable Docker containers.

    Args:
        location (str): The directory where the README.md file will be saved.
        subnet (str): The subnet in which the Docker containers are located, formatted as 'xx.xx.xx'.
        containers (list): A list of container identifiers. The number of identifiers determines the number of reachable IP addresses to list.

    Returns:
        None

    Raises:
        OSError: If there is an error creating the directory or writing the file.
    """

    readme_content = """
    # OpenVPN Connection Instructions

    To connect to the desired subnet, use the following command: "sudo openvpn client.ovpn" 

    Once connected, you can only reach the Docker containers within the subnet. The possible reachable IP addresses with `ping` are:

    - {subnet}.1
    - {subnet}.2
    """.strip().format(subnet=subnet)

    # Add the reachable container IP addresses based on the length of the containers list
    for i in range(1, len(containers) + 1):
        readme_content += f"\n    - {subnet}.{2 + i}"

    # Ensure the directory exists
    os.makedirs(location, exist_ok=True)

    # Write the README.md file to the specified location
    readme_file_path = os.path.join(location, "README.md")
    try:
        with open(readme_file_path, 'w') as readme_file:
            readme_file.write(readme_content.strip())
    except OSError as e:
        print(f"Error writing README.md file: {e}")
        raise
