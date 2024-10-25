from ipaddress import ip_network
import sys
import os

sys.path.append(os.getcwd())
from src.log_config import get_logger


logger = get_logger("ctf_creator.participant")


class Participant:
    def __init__(self, user: str, save_path: str) -> None:
        self.name = user
        self.save_path = save_path
        if os.path.exists(f"{self.save_path}/data/{self.name}"):
            self.ip, self.existing_openvpn_port = self._extract_ovpn_info(
                f"{self.save_path}/data/{self.name}/client.ovpn"
            )
            self.subnet = ip_network(
                self._extract_readme_info(
                    f"{self.save_path}/data/{self.name}/README.md"
                )
            )

    def _extract_readme_info(self, file_path):
        """
        Extracts the host IP address, port number, and subnet from an OpenVPN configuration file.

        Args:
            file_path (str): Path to the OpenVPN configuration file.

        Returns:
            tuple: A tuple containing:
                - host_ip_address (str): The IP address found after the 'remote' keyword.
                - port_number (int): The port number found after the IP address on the 'remote' line.
        """
        if not os.path.exists(file_path):
            logger.error(f"File {file_path} does not exist.")
            return None

        subnet = None

        with open(file_path, "r") as file:
            lines = file.readlines()

        for line in lines:
            if line.startswith("Your subnet is: "):
                parts = line.split(": ")
                if len(parts) == 2:
                    subnet = parts[1].replace("\n", "")

        return subnet

    def _extract_ovpn_info(self, file_path):
        """
        Extracts the host IP address, port number, and subnet from an OpenVPN configuration file.

        Args:
            file_path (str): Path to the OpenVPN configuration file.

        Returns:
            tuple: A tuple containing:
                - host_ip_address (str): The IP address found after the 'remote' keyword.
                - port_number (int): The port number found after the IP address on the 'remote' line.
        """
        if not os.path.exists(file_path):
            logger.error(f"File {file_path} does not exist.")
            return None

        host_ip_address = None
        port_number = None

        with open(file_path, "r") as file:
            lines = file.readlines()

        for line in lines:
            if line.startswith("remote "):
                parts = line.split()
                if len(parts) == 3:
                    host_ip_address = parts[1]
                    port_number = int(parts[2])

        if host_ip_address and port_number:
            return host_ip_address, port_number
        else:
            logger.error("Failed to extract all necessary information.")
            return None

    def write_readme(self) -> None:
        with open(
            f"{os.path.dirname(os.path.realpath(__file__))}/README.md.template", "r"
        ) as file:
            readme_content = file.read()

        readme_content = readme_content.format(user=self.name, subnet=self.subnet)

        logger.debug(
            "Add the reachable container IP addresses based on the length of the containers list"
        )
        path = f"{self.save_path}/data/{self.name}"

        logger.debug("Ensure the directory exists")
        os.makedirs(path, exist_ok=True)

        logger.debug("Write the README.md file to the specified location.")
        readme_file_path = os.path.join(path, "README.md")
        try:
            with open(readme_file_path, "w") as readme_file:
                readme_file.write(readme_content.strip())
        except OSError as e:
            logger.error(f"Error writing README.md file: {e}")
            raise
