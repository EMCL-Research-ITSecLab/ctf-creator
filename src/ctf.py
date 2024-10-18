import os
import sys
from typing import List
import yamale
import click
import pathlib

from ipaddress import ip_network
from yamale import YamaleError
from yamale.validators import DefaultValidators

sys.path.append(os.getcwd())
from src.host import Host
from src.log_config import get_logger
from src.utils import Path


logger = get_logger("ctf_creator.ctf")


class CTFCreator:
    def __init__(self, config: str, save_path: str) -> None:
        self.config = self._get_config(config)
        logger.info(f"Containers: {self.config.get('containers')}")
        logger.info(f"Users: {self.config.get('users')}")
        logger.info(f"Key: {self.config.get('key')}")
        logger.info(f"Hosts: {self.config.get('hosts')}")
        logger.info(f"IP-Address Subnet-base: {self.config.get('subnet')} ")

        self.save_path = save_path
        self.subnet = ip_network(self.config.get("subnet"))

    def _get_config(self, config: dict) -> dict:
        try:
            validators = DefaultValidators.copy()  # This is a dictionary
            validators[Path.tag] = Path
            schema = yamale.make_schema(
                f"{pathlib.Path(__file__).parent.resolve()}/schema.yaml",
                validators=validators,
            )
            # Create a Data object
            data = yamale.make_data(content=config)
            # Validate data against the schema. Throws a ValueError if data is invalid.
            yamale.validate(schema, data)

            logger.info("YAML file loaded successfully.")

            return data[0][0]
        except YamaleError as e:
            logger.error("Validation failed!\n")
            for result in e.results:
                logger.error(
                    "Error validating data '%s' with '%s'\n\t"
                    % (result.data, result.schema)
                )
                for error in result.errors:
                    logger.error("\t%s" % error)
            exit(1)

    def _get_hosts(self) -> List:
        hosts = []
        for host in self.config.get("hosts"):
            host_object = Host(host=host, save_path=self.save_path)
            hosts.append(host_object)
            host_object.clean_up()
        return hosts

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

    def _write_readme(self, path: str, subnet: str, containers: List):
        with open(
            f"{os.path.dirname(os.path.realpath(__file__))}/README.md.template", "r"
        ) as file:
            readme_content = file.read()

        readme_content = readme_content.format(subnet=subnet)

        logger.debug(
            "Add the reachable container IP addresses based on the length of the containers list"
        )
        for i in range(1, len(containers) + 1):
            readme_content += f"\n- {subnet}.{2 + i}"

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

    def create_challenge(self):
        logger.info("Set up hosts.")
        self.hosts = self._get_hosts()
        logger.info("Begin set up of challenge.")

        http_port = 40000
        openvpn_port = 50000
        challenge_counter = 1
        next_network = self.subnet

        ports_in_use = []
        for idx, user in enumerate(self.config.get("users")):
            if os.path.exists(f"{self.save_path}/data/{user}"):
                logger.info(f"Check ports for user: {user}")
                _, existing_openvpn_port = self._extract_ovpn_info(
                    f"{self.save_path}/data/{user}/client.ovpn"
                )
                ports_in_use.append(existing_openvpn_port)
        logger.info(f"Ports in use: {ports_in_use}")

        for idx, user in enumerate(self.config.get("users")):
            in_use = True
            while in_use:
                if not (openvpn_port + challenge_counter) in ports_in_use:
                    in_use = False
                else:
                    challenge_counter += 1

            if os.path.exists(f"{self.save_path}/data/{user}"):
                logger.info(f"OpenVPN data exists for the user: {user}")
                logger.info(
                    f"Data for the user: {user} will NOT be changed. Starting OVPN Docker container with existing data."
                )
                ip, existing_openvpn_port = self._extract_ovpn_info(
                    f"{self.save_path}/data/{user}/client.ovpn"
                )

                logger.info(f"Get host with IP {ip}")
                host: Host = [d for d in self.hosts if str(d.ip) == ip][0]

                host.send_and_extract_tar(user=user)

                host.start_openvpn(
                    user=user,
                    openvpn_port=existing_openvpn_port,
                    http_port=http_port,
                    subnet=next_network,
                )

            else:
                logger.info(
                    f"For the user: {user}, an OpenVPN configuration file will be generated!"
                )
                host: Host = self.hosts[idx % len(self.hosts)]
                host.start_openvpn(
                    user=user,
                    openvpn_port=openvpn_port + challenge_counter,
                    http_port=http_port + challenge_counter,
                    subnet=next_network,
                )

            for idx, container in enumerate(self.config.get("containers")):
                host.start_container(
                    user=user, container=container, subnet=next_network, index=idx
                )

            self._write_readme(
                path=f"{self.save_path}/data/{user}/",
                subnet=next_network,
                containers=self.config.get("containers"),
            )

            next_network = ip_network(
                (int(next_network.network_address) + next_network.num_addresses),
                strict=False,
            )
            next_network = next_network.supernet(new_prefix=24)
            challenge_counter += 1


@click.command()
@click.option(
    "--config",
    required=True,
    help="The path to the .yaml configuration file for the CTF-Creator.",
    type=click.File("r", encoding="utf8"),
)
@click.option(
    "--save",
    required=True,
    help="The path where you want to save the user data for the CTF-Creator. E.g. /home/debian/ctf-creator",
    type=click.Path(writable=True),
)
def main(config, save):
    ctfcreator = CTFCreator(config=config.read(), save_path=save)
    ctfcreator.create_challenge()


if __name__ == "__main__":
    main()
