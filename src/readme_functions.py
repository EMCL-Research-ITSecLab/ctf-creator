import os

def write_readme_for_ovpn_connection(location, subnet, containers):
    """
    Write a README.md file to the specified location with details about connecting to the subnet.

    Parameters:
    - location (str): The directory where the README.md file will be saved.
    - subnet (str): The subnet in which the Docker containers are located.
    - containers (list): A list of container identifiers (length of this list determines reachable IPs).
    """

    readme_content = f"""
    # OpenVPN Connection Instructions

    To connect to the desired subnet, use the following command: "sudo openvpn client.ovpn" 

    Once connected, you can only reach the Docker containers within the subnet. The possible reachable IP addresses with `ping` are:

    - {subnet}.1
    - {subnet}.2
    """

    # Add the reachable container IP addresses based on the length of the containers list
    for i in range(1, len(containers) + 1):
        readme_content += f"- {subnet}.{2 + i}\n"

    # Ensure the directory exists
    os.makedirs(location, exist_ok=True)

    # Write the README.md file to the specified location
    readme_file_path = os.path.join(location, "README.md")
    with open(readme_file_path, 'w') as readme_file:
        readme_file.write(readme_content.strip())

