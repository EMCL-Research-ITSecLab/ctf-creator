from ipaddress import ip_address
import sys
import os
import time

from subprocess import run, CalledProcessError
from docker import DockerClient, from_env
from docker.errors import NotFound, APIError, ImageNotFound
from docker.types import EndpointConfig, IPAMPool, IPAMConfig

sys.path.append(os.getcwd())
from src.log_config import get_logger

logger = get_logger("ctf_creator.docker")

class DownloadError(Exception):
    """Custom exception for download errors."""

    pass

class RemoteLineNotFoundError(Exception):
    """Custom exception raised when no 'remote' line is found in the OpenVPN configuration file."""

    pass

class Docker():
    def __init__(self, host: dict) -> None:
        self.username = host.get("username")
        self.ip = ip_address(host.get("ip"))
        self.client = DockerClient(base_url=f"ssh://{self.username}@{self.ip}")
    
    def prune(self):
        try:
            self.client.containers.prune()
            # Stop all containers and remove them.
            for item in self.client.containers.list(ignore_removed=True):
                try:
                    self.client.containers.prune()
                    item.stop()
                    item.remove(force=True)
                except NotFound:
                    logger.error(
                        f"Container {item.id} not found. It might have been removed already. But it is ok."
                    )
            # Delete all docker networks
            self.client.networks.prune()
        except APIError as api_err:
            raise RuntimeError(
                f"An error occurred while fetching the Docker API version on host {self.ip}. "
                f"This may indicate that Docker is not installed, not running, or not properly configured on the host. "
                f"Please verify the following: "
                f"1. Docker is installed and running on the host by using the command: 'docker info'. "
                f"2. The Docker daemon is configured to accept remote connections if you are accessing it remotely. "
                f"3. Network connectivity to the Docker daemon is not blocked by a firewall or network policy. "
                f"4. You can run Docker commands on the remote host without needing `sudo` privileges, or if `sudo` is required, ensure proper permissions are set. "
                f"5. Check Docker's listening ports with commands such as 'sudo netstat -lntp | grep dockerd'. "
                f"6. Check the CTF-creators README.md for more instructions. "
                f"Original error: {api_err.explanation}"
            )
        except Exception as e:
            raise RuntimeError(
                f"An unexpected error occurred while connecting to Docker on host {self.ip}. "
                f"This may indicate that Docker is not installed, not running, or not properly configured on the host. "
                f"Please verify the following: "
                f"1. Docker is installed and running on the host by using the command: 'docker info'. "
                f"2. The Docker daemon is configured to accept remote connections if you are accessing it remotely. "
                f"3. Network connectivity to the Docker daemon is not blocked by a firewall or network policy. "
                f"4. You can run Docker commands on the remote host without needing `sudo` privileges, or if `sudo` is required, ensure proper permissions are set. "
                f"5. Check Docker's listening ports with commands such as 'sudo netstat -lntp | grep dockerd'. "
                f"6. Check the CTF-creators README.md for more instructions. "
                f"Original error: {e}"
            )
    
    def create_container(self, network_name, name, image):
        """
        Create a Docker container with a specific name, image, and static IP address.

        Args:
            network_name (str): The name of the network to connect the container to.
            name (str): The name of the container to create (must be unique).
            image (str): The Docker image to use for the container.

        Returns:
            docker.models.containers.Container: The created Docker container.

        Raises:
            docker.errors.APIError: If an error occurs during the container creation process.
        """
        try:
            container = self.client.containers.run(
                image,
                detach=True,
                name=name,
                network=network_name,
                networking_config={network_name: self.endpoint_config},
            )
            return container
        except APIError as e:
            logger.error(f"Error creating container: {e}")
            raise
    
    def _curl_client_ovpn(
        self,
        user: str,
        http_port: str,
        save_path: str,
        max_retries_counter=0,
        max_retries=10,
    ) -> None:
        """
        Downloads a .conf version of the client OpenVPN configuration file from a specified URL with retry logic.

        Args:
            user (str): Name of the user.
            http_port (str): Name of the user.
            save_path (str): Path to the directory where the file will be saved.
            max_retries_counter (int, optional): Current retry attempt count.
            max_retries (int, optional): Maximum number of retry attempts.
        """
        save_directory = f"{save_path}/data/{user}"
        url = f"http://{self.ip}:{http_port}/client.ovpn"

        try:
            os.makedirs(save_directory, exist_ok=True)
            command = f"curl -o {save_directory}/client.ovpn {url}"

            while max_retries_counter < max_retries:
                try:
                    run(command, shell=True, check=True)
                    logger.info(f"File downloaded successfully to {save_directory}/client.ovpn")
                    return
                except CalledProcessError:
                    max_retries_counter += 1
                    time.sleep(3)
                    logger.info(f"Retrying... ({max_retries_counter}/{max_retries})")
                except Exception as e:
                    logger.error(f"Unexpected error: {e}")
                    max_retries_counter += 1
                    time.sleep(3)
                    logger.info(f"Retrying... ({max_retries_counter}/{max_retries})")

            logger.info(f"Download failed after {max_retries} retries.")
            raise DownloadError("Max retries exceeded.")

        except Exception as e:
            logger.error(f"Error: An unexpected error occurred - {e}")
            raise DownloadError(f"An unexpected error occurred - {e}")

    def get_openvpn_config(self, user: str, http_port: int, save_path: str):
        logger.info(f"Downloading OpenVPN configuration for {user}...")
        container_name = f"{user}_openvpn"
        
        # Download the folder with data
        try:
            container = self.client.containers.get(container_name)
        except NotFound:
            logger.error(f"Error: Container {container_name} not found.")
            exit(1)
        except Exception as e:
            logger.error(f"Error: Something is wrong with {container_name}. {e}")
            exit(1)

        try:
            logger.info("Executing command in container...")
            _, _ = container.exec_run("./genclient.sh", detach=True)
            # Delay to give time to run the command in the container
            time.sleep(5)
            self._curl_client_ovpn(user=user, http_port=str(http_port), save_path=save_path)
        except Exception as e:
            logger.error(f"Error: Unable to execute command in container. {e}")
            exit(1)
        
        try:
            container = self.client.containers.get(container_name)
            local_save_path = f"{save_path}/data/{user}"
            local_path_to_data = f"{save_path}/data/{user}/dockovpn_data.tar"
            os.makedirs(local_save_path, exist_ok=True)
            archive, stat = container.get_archive("/opt/Dockovpn_data")
            # Save the archive to a local file
            with open(local_path_to_data, "wb") as f:
                for chunk in archive:
                    f.write(chunk)
            logger.info(f"Container found: {container_name}")
            logger.info("And the Dockovpn_data folder is saved on this system")
        except NotFound:
            logger.info(f"Error: Container {container_name} not found.")
            exit(1)
        except Exception as e:
            logger.info(f"Error: Something is wrong with the saving of the ovpn_data!. {e}")
            exit(1)

    def create_openvpn_server(
        self,
        host_address: str,
        network_name: str,
        user: str,
        openvpn_port: int,
        http_port: int,
        mount_path: int,
    ):
        """
        Create an OpenVPN server container with specific configurations.

        Args:
            client (docker.DockerClient): An instance of the Docker client.
            network_name (str): The name of the network to connect the container to.
            name (str): The base name of the OpenVPN server container.

        Returns:
            docker.models.containers.Container: The created OpenVPN server container.

        Raises:
            docker.errors.APIError: If an error occurs during the container creation process.
        """
        self.endpoint_config = EndpointConfig(
            version="1.44", ipv4_address=host_address
        )
        try:
            container = self.client.containers.run(
                image="alekslitvinenk/openvpn",
                detach=True,
                name=f"{user}_openvpn",
                network=network_name,
                restart_policy={"Name": "always"},
                cap_add=["NET_ADMIN"],
                ports={"1194/udp": str(openvpn_port), "8080/tcp": str(http_port)},
                environment={
                    "HOST_ADDR": f"{str(self.ip)}",
                },
                networking_config={network_name: self.endpoint_config},
                volumes=[f"{mount_path}:/opt/Dockovpn_data"]
            )
            
            return container
        except APIError as e:
            logger.error(f"Error creating container: {e}")
            raise

    def create_network(self, name, subnet_, gateway_):
        """
        Create a Docker network with specific IPAM configuration.

        Args:
            name (str): The name of the network to create.
            subnet_ (str): The subnet to use for the network (e.g., '192.168.1.0/24').
            gateway_ (str): The gateway to use for the network (e.g., '192.168.1.1').

        Returns:
            docker.models.networks.Network: The created Docker network.

        Raises:
            docker.errors.APIError: If an error occurs during the network creation process.
        """
        ipam_pool = IPAMPool(subnet=subnet_, gateway=gateway_)
        ipam_config = IPAMConfig(pool_configs=[ipam_pool])

        # Create the network with IPAM configuration
        return self.client.networks.create(
            name, driver="bridge", ipam=ipam_config, check_duplicate=True
        )

    def check_image_existence(image_name):
        """Checks if a Docker image exists in a remote registry using the Docker SDK for Python.
        Otherwise it checks if this image can be pulled.

        Args:
            image_name (str): The name of the image to check.

        Returns:
            bool: True if the image exists, False otherwise.

        Raises:
            docker.errors.ImageNotFound: If the image is not found in the remote registry.
        """

        try:
            local_client = from_env()

            # Attempt to inspect the image locally
            local_client.images.get(f"{image_name}")
            logger.info(f"Image {image_name} exists locally.")
            return True
        except ImageNotFound:
            # If the image is not local, try to pull it
            try:
                logger.warning(f"Try to pull Image {image_name}. Could take some time.")
                local_client.images.pull(f"{image_name}")
                logger.warning(f"Image {image_name} pulled successfully.")
                return True
            except ImageNotFound:
                raise ImageNotFound(
                    f"Error: Image {image_name} could not be pulled. Does this Docker Image exist?"
                )


    # TODO
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
            logger.info(
                f"IP address and port in the 'remote' line of {file_path} have been successfully modified."
            )
            return username
        else:
            logger.info(
                f"No change needed for {username}. The IP address and port are already correct."
            )
            return None
