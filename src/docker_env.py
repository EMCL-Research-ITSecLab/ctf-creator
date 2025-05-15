from ipaddress import IPv4Network, IPv6Network, ip_address
import sys
import os
import time

from subprocess import run, CalledProcessError
from docker import DockerClient
from docker.errors import NotFound, APIError, ImageNotFound
from docker.types import EndpointConfig, IPAMPool, IPAMConfig

sys.path.append(os.getcwd())
from src.log_config import get_logger

logger = get_logger("ctf_creator.docker")


class Docker:
    def __init__(self, host: dict) -> None:
        self.username = host.get("username")
        self.ip = ip_address(host.get("ip"))
        self.client = DockerClient(
            base_url=f"ssh://{self.username}@{self.ip}", use_ssh_client=True
        )

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

    def create_container(
        self,
        environment: dict,
        network_name: str,
        host_address: str,
        container_name: str,
        image: str,
    ) -> None:
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
        self._check_image_existence(image_name=image)

        endpoint_config = EndpointConfig(version="1.44", ipv4_address=host_address)
        try:
            container = self.client.containers.run(
                image,
                detach=True,
                name=container_name,
                network=network_name,
                networking_config={network_name: endpoint_config},
                environment=environment,
                security_opt=["no-new-privileges"],
                # read_only=True,
                tmpfs={
                    "/var/run": "",
                    "/var/cache": "",
                    "/var/cache/nginx": "",
                    "/tmp": "",
                },
                mem_limit="256m",
                memswap_limit=0,
                restart_policy={"name": "always"},
                cpu_quota=500000,
            )
            return container
        except APIError as e:
            logger.error(f"Error creating container: {e}")
            raise

    def create_kali(
        self,
        command: list,
        network_name: str,
        host_address: str,
        container_name: str,
        image: str,
    ) -> None:
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
        self._check_image_existence(image_name=image)

        endpoint_config = EndpointConfig(version="1.44", ipv4_address=host_address)
        try:
            container = self.client.containers.run(
                image,
                detach=True,
                name=container_name,
                network=network_name,
                networking_config={network_name: endpoint_config},
                command=command,
                cap_add=["NET_ADMIN", "NET_RAW"],
                mem_limit="512m",
                memswap_limit=0,
                restart_policy={"name": "always"},
                cpu_quota=50000,
            )
            return container
        except APIError as e:
            logger.error(f"Error creating container: {e}")
            raise

    def create_openvpn_server(
        self,
        host_address: str,
        network_name: str,
        container_name: str,
        openvpn_port: int,
        mount_path: str,
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
        self._check_image_existence(image_name="alekslitvinenk/openvpn")
        endpoint_config = EndpointConfig(version="1.44", ipv4_address=host_address)
        try:
            container = self.client.containers.run(
                image="alekslitvinenk/openvpn",
                detach=True,
                name=container_name,
                command="-s",
                network=network_name,
                restart_policy={"Name": "always"},
                cap_add=["NET_ADMIN"],
                ports={"1194/udp": str(openvpn_port)},
                environment={
                    "HOST_ADDR": f"{str(self.ip)}",
                },
                tmpfs={
                    "/var/run": "",
                    "/var/cache": "",
                    "/tmp": "",
                },
                networking_config={network_name: endpoint_config},
                volumes=[f"{mount_path}:/opt/Dockovpn_data"],
                mem_limit="256m",
                memswap_limit=0,
                cpu_quota=1000,
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

    def _check_image_existence(self, image_name):
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
            # Attempt to inspect the image locally
            self.client.images.get(f"{image_name}")
            logger.debug(f"Image {image_name} exists locally.")
            return True
        except ImageNotFound:
            # If the image is not local, try to pull it
            try:
                logger.warning(f"Try to pull Image {image_name}. Could take some time.")
                self.client.images.pull(f"{image_name}")
                logger.warning(f"Image {image_name} pulled successfully.")
                return True
            except ImageNotFound:
                raise ImageNotFound(
                    f"Error: Image {image_name} could not be pulled. Does this Docker Image exist?"
                )

    def modify_ovpn_server(self, user: str, subnet: IPv4Network | IPv6Network):

        container = self.client.containers.get(f"{user}_openvpn")
        delete_old = [
            "sed -i '/push \"redirect-gateway/d' /etc/openvpn/server.conf",
            "sed -i '/push \"dhcp-option DNS/d' /etc/openvpn/server.conf",
            f"sed -i '$ a\\push \"route {subnet.network_address} 255.255.255.0\"' >> /etc/openvpn/server.conf",
            "sed -i '$ a\\route-nopull' >> /etc/openvpn/server.conf",
            "sed -i '$ a\\pull-filter ignore redirect-gateway' >> /etc/openvpn/server.conf",
            f"iptables -A INPUT -s {subnet.network_address}/24 -j ACCEPT",
            f"iptables -A OUTPUT -d {subnet.network_address}/24 -j ACCEPT",
            f"""
            sed -i '/iptables -t nat -A POSTROUTING -s 10.8.0.0\\/24 -o $ADAPTER -j MASQUERADE/a \\
            iptables -A INPUT -s {subnet.network_address}/24 -j ACCEPT\\n\\
            iptables -A OUTPUT -d {subnet.network_address}/24 -j ACCEPT\\n\\
            iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT\\n\\
            iptables -A OUTPUT -m state --state ESTABLISHED,RELATED -j ACCEPT\\n\\
            iptables -A INPUT -j DROP\\n\\
            iptables -A OUTPUT -j DROP' /opt/Dockovpn/start.sh
            """,
        ]
        for sed_cmd in delete_old:
            container.exec_run(cmd=sed_cmd)

        container.restart()
