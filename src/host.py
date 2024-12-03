import re
import sys
import os
from typing import List

from docker.errors import APIError
from ipaddress import IPv4Network, IPv6Network
from paramiko import SSHClient, AutoAddPolicy
from ipaddress import ip_address
from subprocess import run, PIPE, TimeoutExpired

sys.path.append(os.getcwd())
from src.log_config import get_logger
from src.docker_env import Docker

logger = get_logger("ctf_creator.host")


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
        output, _ = self._execute_ssh_command(command="docker ps -a --format '{{.Names}}'")
        self.containers = output.replace("\r", "").split("\n")
        logger.info(f"Running containers: {self.containers}")

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
            stdin, stdout, stderr = ssh.exec_command(command, get_pty=True)
            # Read the output and error streams
            output = stdout.read().decode()
            error = stderr.read().decode()

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

    def get_container(self, user, container):
        user_filtered = re.sub("[^A-Za-z0-9]+", "", user)
        try:
            for con in self.containers:
                if f"{user_filtered}_{container}" in con:
                    return self.docker.client.containers.get(con)
            logger.warning(
                f"Container not found {user_filtered}_{container} on host {self.ip}"
            )
            return None
        except APIError:
            logger.warning(
                f"Could not find {user_filtered}_{container} on host {self.ip}"
            )
            return None

    def container_exists(self, user, container):
        user_filtered = re.sub("[^A-Za-z0-9]+", "", user)
        for con in self.containers:
            if f"{user_filtered}_{container}" in con:
                return True
        logger.warning(
            f"Container not found {user_filtered}_{container} on host {self.ip}"
        )
        return False

    def container_remove(self, user, container):
        user_filtered = re.sub("[^A-Za-z0-9]+", "", user)
        try:
            pcontainer = self.docker.client.containers.get(f"{user_filtered}_{container}")
            pcontainer.remove(force=True)
        except APIError as e:
            logger.warning(
                f"Container {user_filtered}_{container} not found on host {self.ip}."
            )
            logger.warning(f"Error {e}.")

    def challenge_remove(self, user: str):
        user_filtered = re.sub("[^A-Za-z0-9]+", "", user)
        try:
            for test_container in self.containers:
                if f"{user_filtered}_main-" in test_container:
                    pcontainer = self.docker.client.containers.get(test_container)
                    pcontainer.stop()
                    pcontainer.remove(force=True)
        except APIError as e:
            logger.warning(
                f"Container {user_filtered} not found on host {self.ip}."
            )
            logger.warning(f"Error {e}.")

    def network_remove(self, user):
        user_filtered = re.sub("[^A-Za-z0-9]+", "", user)
        try:
            network = self.docker.client.networks.get(f"{user_filtered}_network")
            network.remove()
        except APIError as e:
            logger.warning(f"Network {user_filtered}_network not found.")
            logger.warning(f"Error {e}.")

    def start_openvpn(
        self,
        user: str,
        openvpn_port: int,
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
            mount_path=f"/home/{self.username}/ctf-data/{user}/Dockovpn_data/",
        )

        self.docker.modify_ovpn_server(user=user_filtered, subnet=subnet)

    def start_container(
        self,
        user: str,
        container: dict,
        subnet: IPv4Network | IPv6Network,
        index: int,
        environment: dict,
    ) -> None:
        user_filtered = re.sub("[^A-Za-z0-9]+", "", user)
        environment["USER_FILTERED"] = user_filtered
        self.docker.create_container(
            environment=environment,
            container_name=f"{user_filtered}_{container['name']}",
            network_name=f"{user_filtered}_network",
            image=container["image"],
            host_address=str(subnet.network_address + index),
        )

    def start_kali(
        self, user: str, subnet: IPv4Network | IPv6Network, index: int, command: list
    ) -> None:
        user_filtered = re.sub("[^A-Za-z0-9]+", "", user)
        self.docker.create_kali(
            command=command,
            container_name=f"{user_filtered}_kali",
            network_name=f"{user_filtered}_network",
            image="ghcr.io/emcl-research-itseclab/itsec-1-exercises:main-kali",
            host_address=str(subnet.network_address + index),
        )
