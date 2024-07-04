"""
This module provides functionalities to establish SSH connections, execute commands, and transfer files to a remote server using Paramiko.

The main functionalities include:
1. Establishing SSH connections using key-based authentication.
2. Executing commands on the remote server.
3. Executing Python code on the remote server.
4. Transferring Python scripts to the remote server.
5. Closing SSH connections.

Functions:
- establish_ssh_connection(hostname, port, username, key_filename): Establishes an SSH connection to the server.
- execute_command_ssh(ssh_client, command): Executes a command on the remote machine using the SSH client.
- execute_python_ssh(ssh_client, python_code): Executes Python code on the remote machine and prints the output.
- send_python_script(ssh_client, script_path, remote_path): Transfers a Python script to the remote machine.
- close_ssh_connection(ssh_client): Closes the SSH connection.
- bastion_command(my_network, host_ip, ip_address): Builds and returns the bastion command for running Docker on a host connected to an SSH server.
"""

import paramiko

def establish_ssh_connection(hostname, port, username, key_filename):
    """
    Establish an SSH connection to the server and return an object to interact with the server. This is a wrapper around paramiko.SSHClient.
    
    Args:
        hostname: The hostname of the server to connect to.
        port: The port of the server to connect to.
        username: The username of the user to connect to the server.
        key_filename: The path to the private key file.
    
    Returns:
        An object to interact with the server or None if the connection failed.
    """
    # Create an SSH client
    ssh_client = paramiko.SSHClient()

    # Automatically add host keys without requiring user confirmation
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # Load the private key file
        private_key = paramiko.Ed25519Key.from_private_key_file(key_filename)

        # Connect to the SSH server using key-based authentication
        ssh_client.connect(hostname=hostname, port=port, username=username, pkey=private_key)
        print("SSH connection established successfully!")

        # Perform operations here (e.g., execute commands, transfer files)

        return ssh_client  # Return the SSH client object

    except paramiko.AuthenticationException:
        print("Authentication failed. Please check your credentials.")
    except paramiko.SSHException as e:
        print(f"SSH connection failed: {e}")

    # If connection fails, return None
    return None

def execute_command_ssh(ssh_client, command):
    """
    Execute a command on the remote machine using the SSH client.
    
    Args:
        ssh_client: The SSH client to use for execution.
        command: The command to execute on the remote machine.
    """

    # Execute the command on the remote machine
    stdin, stdout, stderr = ssh_client.exec_command(command)
        
    # Read the output of the command
    output = stdout.read().decode()
        
    print(stderr.read().decode())
    # Print the output
    print("Output of the command:")
    print(output)

def execute_python_ssh(ssh_client, python_code):
    """
    Execute Python code on the remote machine and print the output. This is a helper function.
    
    Args:
        ssh_client: The SSH client to use for execution.
        python_code: Python code to execute on the remote machine.
    """
    # Execute the Python code on the remote machine
    stdin, stdout, stderr = ssh_client.exec_command(f'python3 -c "{python_code}"')

    # Print the output of the executed Python code
    print(stdout.read().decode())
    print(stderr.read().decode())

def send_pyhton_script(ssh_client, script_path, name):
    """
    Send a Python script to a remote machine.
    
    Args:
        ssh_client: The SSH client to connect to the remote machine.
        script_path: The path to the Python script on the local machine.
        remote_path: The path on the remote machine where the script will be saved.
    """
    # Open an SFTP session
    sftp = ssh_client.open_sftp()

    # Upload the Python script to the remote machine
    sftp.put(script_path, name)

    # Close the SFTP session
    sftp.close()


def close_ssh_connection(ssh_client):
    """
    Close the SSH connection.
    
    Args:
        ssh_client: The SSH client to close the connection.
    """
    # Close the SSH connection to the SSH server.
    if ssh_client:
        # Close the SSH connection
        ssh_client.close()
        print("SSH connection closed successfully!")
    else:
        print("No active SSH connection to close.")


def bastion_command(my_network, host_ip, ip_adress ):
    """
    Build and return the bastion command. This is used to run Docker on a host that is connected to an SSH server.
    
    Args:
        my_network: The name of the network to connect to.
        host_ip: The IP address of the host to connect to.
        ip_address: The IPv4 or IPv6 address of the host to connect to.
    
    Returns:
        A command string to run on the Docker host with bastion and SSH.
    """
    return f"""

    docker run -d \
        --name bastion \
        --hostname bastion \
        --restart unless-stopped \
        -v $PWD/authorized_keys:/var/lib/bastion/authorized_keys:ro \
        -v bastion:/usr/etc/ssh:rw \
        --add-host docker-host:{host_ip} \
        --network = {my_network} \
        --ip {ip_adress} \
        -p 22222:22/tcp \
        -e "PUBKEY_AUTHENTICATION=true" \
        -e "GATEWAY_PORTS=false" \
        -e "PERMIT_TUNNEL=false" \
        -e "X11_FORWARDING=false" \
        -e "TCP_FORWARDING=true" \
        -e "AGENT_FORWARDING=true" \
        binlab/bastion
        
        """

                




