import re
import sys
import os
from typing import List

from ipaddress import IPv4Network, IPv6Network
from paramiko import SSHClient, AutoAddPolicy
from ipaddress import ip_address
from subprocess import run, PIPE, TimeoutExpired

sys.path.append(os.getcwd())
from src.log_config import get_logger
from src.docker_env import Docker

logger = get_logger("ctf_creator.host")


class RemoteLineNotFoundError(Exception):
    """Custom exception raised when no 'remote' line is found in the OpenVPN configuration file."""

    pass


class Host:
    def __init__(self, host: dict, save_path: str) -> None:
        self.host = host
        self.username = host.get("username")
        self.ip = ip_address(host.get("ip"))
        logger.info(f"Check connection for {self.username}@{self.ip}")

        self.identify_path = host.get("identity_file")
        if not os.path.isfile(self.identify_path):
            raise FileNotFoundError(f"Identity file not found: {self.identify_path}.")

        self._check_reachability()
        self._check_ssh()
        self._add_ssh_identity()

        self.docker = Docker(host=host)
        self.save_path = save_path

    def _check_reachability(self):
        """
        Checks the reachability of a host using the ping command.

        Args:
            host_ips (list of str): List of host IP addresses to check.

        Raises:
            SystemExit: If any host is unreachable, prints the unreachable hosts and exits the program.
        """
        try:
            run(
                ["ping", "-c", "1", str(self.ip)],
                stdout=PIPE,
                stderr=PIPE,
            )
        except Exception as e:
            logger.error(f"Error pinging host {self.ip}: {e}")
            raise

    def _check_ssh(self):
        """
        Checks SSH connectivity and credentials for a given host. Helper function.

        Args:
            self.ip (str): Host information in the format 'user@host'.

        Returns:
            bool: True if SSH connection is successful, False otherwise.
        """
        try:
            # Attempt to SSH into the host
            result = run(
                ["ssh", "-i", self.identify_path, f"{self.username}@{self.ip}", "exit"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                if "Permission denied" in result.stderr:
                    logger.error(
                        f"SSH connection to {self.ip} failed due to incorrect username or password."
                    )
                else:
                    logger.error(f"SSH connection to {self.ip} failed: {result.stderr}")
                return False
            return True
        except TimeoutExpired:
            logger.error(f"SSH connection to {self.ip} timed out.")
            return False
        except Exception as e:
            logger.error(f"Error attempting SSH connection to {self.ip}: {e}")
            return False

    def _execute_ssh_command(self, command):
        """
        Executes a command on a remote host via SSH.

        Args:
            command (str): The command to execute on the remote host.

        Returns:
            tuple: A tuple containing the command's output and error messages.
        """

        # Create an SSH client
        ssh = SSHClient()

        # Load SSH host keys
        ssh.load_system_host_keys()

        # Add missing host keys
        ssh.set_missing_host_key_policy(AutoAddPolicy())

        try:
            # Connect to the remote host using SSH agent for authentication
            ssh.connect(str(self.ip), port=22, username=self.username)
            # Execute the command
            stdin, stdout, stderr = ssh.exec_command(command)
            # Read the output and error streams
            output = stdout.read().decode()
            error = stderr.read().decode()
            # Print the output and error (if any)
            if output:
                logger.info("Output:\n", output)
            if error:
                logger.error("Error:\n", error)

            return output, error

        except Exception as e:
            logger.error(f"An error occurred: {e}")
            return None, str(e)
        finally:
            # Close the SSH connection
            ssh.close()

    def _add_ssh_identity(self):
        commands = [f'eval "$(ssh-agent)" ', f"ssh-add {self.identify_path}"]

        try:
            # Run all commands in the list of commands
            for command in commands:
                result = run(command, shell=True, executable="/bin/bash")
                if result.returncode != 0:
                    logger.error(f"Error executing command: {command}")
                    break
        except Exception as e:
            raise RuntimeError(f"An unexpected error occurred: {e}")

    def clean_up(self):
        self.docker.prune()
        self._execute_ssh_command(
            f"sudo test -d /home/{self.username}/ctf-data/ && sudo rm -r /home/{self.username}/ctf-data/"
        )
        logger.info("Clean up process on hosts finished!")

    def send_and_extract_tar(self, user: str) -> None:
        """
        Sends a tar file to a remote host via SSH and extracts it.

        Raises:
            PermissionError: If there is a permission issue on the remote host.
        """
        tar_file_path = f"{self.save_path}/data/{user}/dockovpn_data.tar"
        remote_path = f"/home/{self.username}/ctf-data/{user}/dock_vpn_data.tar"

        # Create an SSH client
        ssh = SSHClient()

        # Load SSH host keys
        ssh.load_system_host_keys()

        # Add missing host keys
        ssh.set_missing_host_key_policy(AutoAddPolicy())

        try:
            # Connect to the remote host using SSH agent for authentication
            logger.info(f"Connecting to {self.ip} as {self.username}...")
            ssh.connect(str(self.ip), port=22, username=self.username)

            # Extract the remote directory path
            remote_dir = os.path.dirname(
                f"/home/{self.username}/ctf-data/{user}/Dockovpn_data/"
            )

            # Ensure the remote directory exists
            logger.info(f"Ensuring the remote directory {remote_dir} exists...")
            mkdir_command = f"mkdir -p {remote_dir}"
            _, stdout, stderr = ssh.exec_command(mkdir_command)
            mkdir_error = stderr.read().decode().strip()
            if mkdir_error:
                raise PermissionError(
                    f"Failed to create directory {remote_dir}: {mkdir_error}"
                )
            stdout.channel.recv_exit_status()  # Wait for the command to complete

            # Use SFTP to copy the tar file
            logger.info(f"Copying {tar_file_path} to {self.ip}:{remote_path}...")
            sftp = ssh.open_sftp()
            sftp.put(tar_file_path, remote_path)
            sftp.close()

            logger.info(
                f"File {tar_file_path} successfully sent to {self.ip}:{remote_path}"
            )

            # Ensure correct permissions for the remote path and extract the tar file
            logger.info(f"Extracting tar file {remote_path} on {self.ip}...")
            extract_command = (
                f"tar --strip-components=1 -xf {remote_path} -C {remote_dir}"
            )
            _, stdout, stderr = ssh.exec_command(extract_command)
            stdout.channel.recv_exit_status()  # Wait for the command to complete

            # Read the output and error streams
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()

            # Print the output and error (if any)
            if output:
                logger.info("Output:\n", output)
            if error:
                logger.error("Error:\n", error)
                raise PermissionError(f"Failed to extract tar file: {error}")

        except PermissionError as pe:
            logger.error(f"A permission error occurred: {pe}")
        finally:
            # Close the SSH connection
            logger.info("Closing the SSH connection...")
            ssh.close()

    def start_openvpn(
        self,
        user: str,
        openvpn_port: int,
        http_port: int,
        subnet: IPv4Network | IPv6Network,
    ):
        user_filtered = re.sub("[^A-Za-z0-9]+", "", user)
        self.docker.create_network(
            name=f"{user_filtered}_network",
            subnet_=str(subnet),
            gateway_=str(subnet.network_address + 1),
        )

        self.docker.create_openvpn_server(
            host_address=str(subnet.network_address + 2),
            network_name=f"{user_filtered}_network",
            container_name=f"{user_filtered}_openvpn",
            openvpn_port=openvpn_port,
            http_port=http_port,
            mount_path=f"/home/{self.username}/ctf-data/{user}/Dockovpn_data/",
        )

        if not os.path.exists(f"{self.save_path}/data/{user}"):
            self.docker.get_openvpn_config(
                user=user,
                container_name=f"{user_filtered}_openvpn",
                http_port=http_port,
                save_path=self.save_path,
            )

        self._modify_ovpn_client(user=user, port=openvpn_port)

        self.docker.modify_ovpn_server(user=user_filtered, subnet=subnet)

    def start_container(
        self, user: str, container: dict, subnet: IPv4Network | IPv6Network, index: int, environment: dict
    ) -> None:
        user_filtered = re.sub("[^A-Za-z0-9]+", "", user)
        self.docker.create_container(
            environment=environment,
            container_name=f"{user_filtered}_{container['name']}_" + f"{index}",
            network_name=f"{user_filtered}_network",
            image=container["image"],
            host_address=str(subnet.network_address + index),
        )

    def _modify_ovpn_client(self, user: str, port: int) -> None:
        """
        Changes the IP address and port in the 'remote' line of an OpenVPN configuration file
        only if the IP address or port is different from the current values.

        Args:
            user (str): Username associated with the OpenVPN configuration file.
            port (int): New port number to replace in the 'remote' line.

        Returns:
            str: The username if the configuration was changed, otherwise None.
        """
        if not os.path.exists(f"{self.save_path}/data/{user}/client.ovpn"):
            print(f"File {f'{self.save_path}/data/{user}/client.ovpn'} does not exist.")
            return None

        modified_lines = []

        with open(f"{self.save_path}/data/{user}/client.ovpn", "r") as file:
            lines = file.readlines()

        remote_line_found = False
        change_needed = False

        for line in lines:
            if line.startswith("remote "):
                parts = line.split()
                if len(parts) == 3:
                    current_ip = parts[1]
                    current_port = parts[2]

                    if current_ip != self.ip or current_port != str(port):
                        parts[1] = str(self.ip)
                        parts[2] = str(port)
                        line = " ".join(parts) + "\n"
                        change_needed = True

                    remote_line_found = True

            modified_lines.append(line)

        if not remote_line_found:
            raise RemoteLineNotFoundError("No 'remote' line found in the file.")

        if change_needed:
            with open(f"{self.save_path}/data/{user}/client.ovpn", "w") as file:
                file.writelines(modified_lines)
            logger.info(
                f"IP address and port in the 'remote' line of {f'{self.save_path}/data/{user}/client.ovpn'} have been successfully modified."
            )
        else:
            logger.info(
                f"No change needed for {user}. The IP address and port are already correct."
            )
