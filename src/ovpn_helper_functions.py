"""
This module provides functionality for downloading and modifying OpenVPN configuration files.

Functions:
- curl_client_ovpn_file_version(container, host_address, user_name, counter, save_path, max_retries_counter=0, max_retries=10): Downloads an OpenVPN configuration file from a remote server with retry logic.
- modify_ovpn_file(file_path, new_port, new_route_ip): Modifies an OpenVPN configuration file to update the remote port and add specific route settings.
- modify_ovpn_file_change_host(file_path, new_ip, new_port): Changes the IP address and port in the 'remote' line of an OpenVPN configuration file.
"""

import subprocess
import os
import time
import logging

class DownloadError(Exception):
    """Custom exception for download errors."""

    pass


def curl_client_ovpn_file_version(
    host_address,
    user_name,
    counter,
    save_path,
    max_retries_counter=0,
    max_retries=10,
):
    """
    Downloads a .conf version of the client OpenVPN configuration file from a specified URL with retry logic.

    Args:
        container: Docker container object (unused in this function but kept for consistency).
        host_address (str): Address of the host serving the file.
        user_name (str): Name of the user.
        counter (int): Counter for port calculation.
        save_path (str): Path to the directory where the file will be saved.
        max_retries_counter (int, optional): Current retry attempt count.
        max_retries (int, optional): Maximum number of retry attempts.
    """
    save_directory = f"{save_path}/data/{user_name}"
    url = f"http://{host_address}:{80 + counter}/client.ovpn"

    try:
        os.makedirs(save_directory, exist_ok=True)
        command = f"curl -o {save_directory}/client.ovpn {url}"

        while max_retries_counter < max_retries:
            try:
                subprocess.run(command, shell=True, check=True)
                logging.info(f"File downloaded successfully to {save_directory}/client.ovpn")
                return
            except subprocess.CalledProcessError:
                max_retries_counter += 1
                time.sleep(3)
                logging.info(f"Retrying... ({max_retries_counter}/{max_retries})")
            except Exception as e:
                logging.error(f"Unexpected error: {e}")
                max_retries_counter += 1
                time.sleep(3)
                logging.info(f"Retrying... ({max_retries_counter}/{max_retries})")

        logging.info(f"Download failed after {max_retries} retries.")
        raise DownloadError("Max retries exceeded.")

    except Exception as e:
        logging.error(f"Error: An unexpected error occurred - {e}")
        raise DownloadError(f"An unexpected error occurred - {e}")


class RemoteLineNotFoundError(Exception):
    """Custom exception raised when no 'remote' line is found in the OpenVPN configuration file."""

    pass


def modify_ovpn_file(file_path, new_port, new_route_ip):
    """
    Modifies an OpenVPN configuration file to update the remote port and add specific route settings.

    Args:
        file_path (str): Path to the OpenVPN configuration file.
        new_port (int): New port number to replace in the 'remote' line.
        new_route_ip (str): New IP address for the route setting.
    """
    if not os.path.exists(file_path):
        print(f"File {file_path} does not exist.")
        return

    modified_lines = []

    with open(file_path, "r") as file:
        lines = file.readlines()

    remote_line_found = False

    for line in lines:
        if line.startswith("remote "):
            parts = line.split()
            if len(parts) == 3:
                parts[-1] = str(new_port)
                line = " ".join(parts) + "\n"
                remote_line_found = True

            modified_lines.append(line)
            modified_lines.append("route-nopull\n")
            modified_lines.append(f"route {new_route_ip}\n")
            modified_lines.append('pull-filter ignore "redirect-gateway"\n')
            modified_lines.append('pull-filter ignore "dhcp-option"\n')
            modified_lines.append('pull-filter ignore "route"\n')
        else:
            modified_lines.append(line)

    if not remote_line_found:
        raise RemoteLineNotFoundError("No 'remote' line found in the file.")

    with open(file_path, "w") as file:
        file.writelines(modified_lines)


def modify_ovpn_file_change_host(file_path, new_ip, new_port, username):
    """
    Changes the IP address and port in the 'remote' line of an OpenVPN configuration file
    only if the IP address or port is different from the current values.

    Args:
        file_path (str): Path to the OpenVPN configuration file.
        new_ip (str): New IP address to replace in the 'remote' line.
        new_port (int): New port number to replace in the 'remote' line.
        username (str): Username associated with the OpenVPN configuration file.

    Returns:
        str: The username if the configuration was changed, otherwise None.
    """
    if not os.path.exists(file_path):
        print(f"File {file_path} does not exist.")
        return None

    modified_lines = []

    with open(file_path, "r") as file:
        lines = file.readlines()

    remote_line_found = False
    change_needed = False

    for line in lines:
        if line.startswith("remote "):
            parts = line.split()
            if len(parts) == 3:
                current_ip = parts[1]
                current_port = parts[2]

                if current_ip != new_ip or current_port != str(new_port):
                    parts[1] = str(new_ip)
                    parts[2] = str(new_port)
                    line = " ".join(parts) + "\n"
                    change_needed = True

                remote_line_found = True

        modified_lines.append(line)

    if not remote_line_found:
        raise RemoteLineNotFoundError("No 'remote' line found in the file.")

    if change_needed:
        with open(file_path, "w") as file:
            file.writelines(modified_lines)
        logging.info(
            f"IP address and port in the 'remote' line of {file_path} have been successfully modified."
        )
        return username
    else:
        logging.info(
            f"No change needed for {username}. The IP address and port are already correct."
        )
        return None
