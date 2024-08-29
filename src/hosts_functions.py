"""
This module provides functionalities for managing SSH connections and operations,
including host reachability checks via ping and SSH, executing commands over SSH,
and transferring and extracting tar files on remote hosts.

Functions:
- check_host_reachability_with_ping(host_ips): Checks the reachability of hosts using ping.
- check_ssh_connection(host_info): Verifies SSH connectivity and credentials for a given host.
- check_host_reachability_with_SSH(host_infos): Checks SSH connectivity and credentials for a list of hosts.
- execute_ssh_command(user_host, command, remote_port=22): Executes a command on a remote host via SSH.
- send_and_extract_tar_via_ssh(tar_file_path, host_username, remote_host, remote_path, remote_port=22): Sends a tar file to a remote host and extracts it.
"""

import subprocess
import sys
import time
import os
import paramiko


def check_host_reachability_with_ping(host_ips):
    """
    Checks the reachability of a list of hosts using the ping command.

    Args:
        host_ips (list of str): List of host IP addresses to check.

    Raises:
        SystemExit: If any host is unreachable, prints the unreachable hosts and exits the program.
    """
    unreachable_hosts = []

    for host in host_ips:
        try:
            result = subprocess.run(
                ['ping', '-c', '1', host], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode != 0:
                unreachable_hosts.append(host)
        except Exception as e:
            print(f"Error pinging host {host}: {e}")
            unreachable_hosts.append(host)

    if unreachable_hosts:
        print("The following hosts are unreachable:")
        for host in unreachable_hosts:
            print(f"- {host}")
        print("Please check if you are connected to the correct network to ensure connectivity with these hosts.")
        sys.exit(1)
    else:
        print("All hosts are reachable with ping.")


def check_ssh_connection(host_info):
    """
    Checks SSH connectivity and credentials for a given host. Helper function.

    Args:
        host_info (str): Host information in the format 'user@host'.

    Returns:
        bool: True if SSH connection is successful, False otherwise.
    """
    try:
        # Attempt to SSH into the host
        result = subprocess.run(
            ['ssh', host_info, 'exit'],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            if "Permission denied" in result.stderr:
                print(
                    f"SSH connection to {host_info} failed due to incorrect username or password.")
            else:
                print(f"SSH connection to {host_info} failed: {result.stderr}")
            return False
        return True
    except subprocess.TimeoutExpired:
        print(f"SSH connection to {host_info} timed out.")
        return False
    except Exception as e:
        print(f"Error attempting SSH connection to {host_info}: {e}")
        return False


# Uses also the unsername so you can deduce if the host Ip is wrong or the username!
def check_host_reachability_with_SSH(host_infos):
    """
    Checks SSH connectivity and credentials for a list of hosts.

    Args:
        host_infos (list of str): List of host information in the format 'user@host'.

    Raises:
        SystemExit: If any host has incorrect SSH credentials or is unreachable, prints the problematic hosts and exits the program.
    """
    unreachable_hosts = []

    for host_info in host_infos:
        if not check_ssh_connection(host_info):
            unreachable_hosts.append(host_info)
    time.sleep(1)

    if unreachable_hosts:
        print("The following hosts are unreachable or have incorrect SSH credentials:")
        for host_info in unreachable_hosts:
            print(f"- {host_info}")
        print("Please check if you are connected to the correct network and using the correct SSH host-username.")
        sys.exit(1)
    else:
        print("All SSH connections to hosts were successful.")


def execute_ssh_command(user_host, command, remote_port=22):
    """
    Executes a command on a remote host via SSH.

    Args:
        user_host (str): User and host information in the format 'user@host'.
        command (str): The command to execute on the remote host.
        remote_port (int, optional): The port to use for SSH (default is 22).

    Returns:
        tuple: A tuple containing the command's output and error messages.
    """
    # Parse the user and host from the user_host variable
    username, remote_host = user_host.split('@')

    # Create an SSH client
    ssh = paramiko.SSHClient()

    # Load SSH host keys
    ssh.load_system_host_keys()

    # Add missing host keys
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # Connect to the remote host using SSH agent for authentication
        ssh.connect(remote_host, port=remote_port, username=username)

        # Execute the command
        stdin, stdout, stderr = ssh.exec_command(command)

        # Read the output and error streams
        output = stdout.read().decode()
        error = stderr.read().decode()

        # Print the output and error (if any)
        if output:
            print("Output:\n", output)
        if error:
            print("Error:\n", error)

        return output, error

    except Exception as e:
        print(f"An error occurred: {e}")
        return None, str(e)
    finally:
        # Close the SSH connection
        ssh.close()


def send_and_extract_tar_via_ssh(tar_file_path, host_username, remote_host, remote_path, remote_port=22):
    """
    Sends a tar file to a remote host via SSH and extracts it.

    Args:
        tar_file_path (str): The path to the tar file on the local system.
        host_username (str): The username to use for SSH.
        remote_host (str): The remote host to connect to.
        remote_path (str): The path on the remote host where the tar file will be placed and extracted.
        remote_port (int, optional): The port to use for SSH (default is 22).

    Raises:
        PermissionError: If there is a permission issue on the remote host.
    """

    # Create an SSH client
    ssh = paramiko.SSHClient()

    # Load SSH host keys
    ssh.load_system_host_keys()

    # Add missing host keys
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # Connect to the remote host using SSH agent for authentication
        print(f"Connecting to {remote_host} as {host_username}...")
        ssh.connect(remote_host, port=remote_port, username=host_username)

        # Extract the remote directory path
        remote_dir = os.path.dirname(remote_path)

        # Ensure the remote directory exists
        print(f"Ensuring the remote directory {remote_dir} exists...")
        mkdir_command = f'mkdir -p {remote_dir}'
        stdin, stdout, stderr = ssh.exec_command(mkdir_command)
        mkdir_error = stderr.read().decode().strip()
        if mkdir_error:
            raise PermissionError(
                f"Failed to create directory {remote_dir}: {mkdir_error}")
        stdout.channel.recv_exit_status()  # Wait for the command to complete

        # Use SFTP to copy the tar file
        print(f"Copying {tar_file_path} to {remote_host}:{remote_path}...")
        sftp = ssh.open_sftp()
        sftp.put(tar_file_path, remote_path)
        sftp.close()

        print(
            f"File {tar_file_path} successfully sent to {remote_host}:{remote_path}")

        # Ensure correct permissions for the remote path and extract the tar file
        print(f"Extracting tar file {remote_path} on {remote_host}...")
        extract_command = f'tar -xf {remote_path} -C {remote_dir}'
        stdin, stdout, stderr = ssh.exec_command(extract_command)
        stdout.channel.recv_exit_status()  # Wait for the command to complete

        # Read the output and error streams
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()

        # Print the output and error (if any)
        if output:
            print("Output:\n", output)
        if error:
            print("Error:\n", error)
            raise PermissionError(f"Failed to extract tar file: {error}")

    except PermissionError as pe:
        print(f"A permission error occurred: {pe}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Close the SSH connection
        print("Closing the SSH connection...")
        ssh.close()


def extract_ovpn_info(file_path):
    """
    Extracts the host IP address, port number, and subnet from an OpenVPN configuration file.

    Args:
        file_path (str): Path to the OpenVPN configuration file.

    Returns:
        tuple: A tuple containing:
            - host_ip_address (str): The IP address found after the 'remote' keyword.
            - port_number (int): The port number found after the IP address on the 'remote' line.
            - subnet (str): The subnet extracted from the 'route' line (first three sections of the IP address).
    """
    if not os.path.exists(file_path):
        print(f"File {file_path} does not exist.")
        return None

    host_ip_address = None
    port_number = None
    subnet = None

    with open(file_path, 'r') as file:
        lines = file.readlines()

    for line in lines:
        if line.startswith("remote "):
            parts = line.split()
            if len(parts) == 3:
                host_ip_address = parts[1]
                port_number = int(parts[2])

        if line.startswith("route "):
            parts = line.split()
            if len(parts) >= 2:
                ip_parts = parts[1].split('.')
                if len(ip_parts) >= 3:
                    subnet = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}"

    if host_ip_address and port_number and subnet:
        return host_ip_address, port_number, subnet
    else:
        print("Failed to extract all necessary information.")
        return None
