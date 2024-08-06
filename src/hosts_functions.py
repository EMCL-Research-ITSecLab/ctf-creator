import subprocess
import sys
import time
import os
import paramiko

def check_host_reachability_with_ping(host_ips):
    unreachable_hosts = []
    
    for host in host_ips:
        try:
            result = subprocess.run(['ping', '-c', '1', host], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode != 0:
                unreachable_hosts.append(host)
        except Exception as e:
            print(f"Error pinging host {host}: {e}")
            unreachable_hosts.append(host)
    
    if unreachable_hosts:
        print("The following hosts are unreachable:")
        for host in unreachable_hosts:
            print(f"- {host}")
        print("Please check if you are connected to the correct WireGuard VPN to ensure connectivity with these hosts.")
        sys.exit(1)
    else:
        print("All hosts are reachable with ping.")


def check_ssh_connection(host_info):
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
                print(f"SSH connection to {host_info} failed due to incorrect username or password.")
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
    

#Uses also the unsername so you can deduce if the host Ip is wrong or the username!
def check_host_reachability_with_SSH(host_infos):
    unreachable_hosts = []

    for host_info in host_infos:
        if not check_ssh_connection(host_info):
            unreachable_hosts.append(host_info)
    time.sleep(1)
    
    if unreachable_hosts:
        print("The following hosts are unreachable or have incorrect SSH credentials:")
        for host_info in unreachable_hosts:
            print(f"- {host_info}")
        print("Please check if you are connected to the correct WireGuard VPN and using the correct SSH host-username.")
        sys.exit(1)
    else:
        print("All SSH connections to hosts were successful.")

def send_tar_file_via_ssh(tar_file_path, host_username, remote_host, remote_path, remote_port=22):
    # Parse the user and host from the user_host variable
    
    # Create an SSH client
    ssh = paramiko.SSHClient()
    
    # Load SSH host keys
    ssh.load_system_host_keys()
    
    # Add missing host keys
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # Connect to the remote host using SSH agent for authentication
        ssh.connect(remote_host, port=remote_port, username=host_username)
        
        # Extract the remote directory path
        remote_dir = os.path.dirname(remote_path)
        
        # Ensure the remote directory exists
        stdin, stdout, stderr = ssh.exec_command(f'mkdir -p {remote_dir}')
        stdout.channel.recv_exit_status()  # Wait for the command to complete
        
        # Use SFTP to copy the file
        sftp = ssh.open_sftp()
        sftp.put(tar_file_path, remote_path)
        sftp.close()
        
        print(f"File {tar_file_path} successfully sent to {remote_host}:{remote_path}")
        
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Close the SSH connection
        ssh.close()


def execute_ssh_command(user_host, command, remote_port=22):
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
    # Create an SSH client
    ssh = paramiko.SSHClient()
    
    # Load SSH host keys
    ssh.load_system_host_keys()
    
    # Add missing host keys
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # Connect to the remote host using SSH agent for authentication
        ssh.connect(remote_host, port=remote_port, username=host_username)
        
        # Extract the remote directory path
        remote_dir = os.path.dirname(remote_path)
        
        # Ensure the remote directory exists
        stdin, stdout, stderr = ssh.exec_command(f'sudo mkdir -p {remote_dir}')
        stdout.channel.recv_exit_status()  # Wait for the command to complete
        
        # Use SFTP to copy the tar file
        sftp = ssh.open_sftp()
        sftp.put(tar_file_path, remote_path)
        sftp.close()
        
        print(f"File {tar_file_path} successfully sent to {remote_host}:{remote_path}")
        
        # Extract the tar file on the remote host
        extract_command = f'sudo tar -xf {remote_path} -C {remote_dir}'
        stdin, stdout, stderr = ssh.exec_command(extract_command)
        stdout.channel.recv_exit_status()  # Wait for the command to complete
        
        # Read the output and error streams
        output = stdout.read().decode()
        error = stderr.read().decode()
        
        # Print the output and error (if any)
        if output:
            print("Output:\n", output)
        if error:
            print("Error:\n", error)
        
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Close the SSH connection
        ssh.close()


def send_and_extract_tar_via_ssh_v2(tar_file_path, host_username, remote_host, remote_path, remote_port=22):
   
    
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
            raise PermissionError(f"Failed to create directory {remote_dir}: {mkdir_error}")
        stdout.channel.recv_exit_status()  # Wait for the command to complete
        
        # Use SFTP to copy the tar file
        print(f"Copying {tar_file_path} to {remote_host}:{remote_path}...")
        sftp = ssh.open_sftp()
        sftp.put(tar_file_path, remote_path)
        sftp.close()
        
        print(f"File {tar_file_path} successfully sent to {remote_host}:{remote_path}")
        
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