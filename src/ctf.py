import os
import random
import sys
from typing import List
import yamale
import click
import pathlib

from ipaddress import IPv4Network, IPv6Network, ip_network
from yamale import YamaleError
from yamale.validators import DefaultValidators

sys.path.append(os.getcwd())
from src.host import Host
from src.log_config import get_logger
from src.utils import Path


logger = get_logger("ctf_creator.ctf")


class CTFCreator:
    def __init__(self, config: str, save_path: str, prune: bool) -> None:
        self.config = self._get_config(config)
        self.prune = prune
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
            logger.info(f"Clean up for host {host}")
            host_object = Host(host=host, save_path=self.save_path)
            hosts.append(host_object)
            if self.prune:
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
    
    def _check_running(self, user: str, host: Host):
        logger.info("Check if containers and OpenVPN exists...")
        
        running=True
        for test_container in self.config.get("containers"):
            container_name = test_container['name']
            if not host.container_exists(user=user, container=container_name):
                running = False
        if not host.container_exists(user=user, container="openvpn"):
            running = False

        if running:
            logger.info(f"All are up and running for {user}")
        if not running:
            logger.info(f"Remove containers, not all are up and running for {user}")
            host.container_remove(user=user, container="openvpn")
            for test_container in self.config.get("containers"):
                container_name = test_container['name']
                host.container_remove(user=user, container=container_name)
            host.network_remove(user=user)

        return running

    def create_challenge(self):
        logger.info("Set up hosts.")
        self.hosts = self._get_hosts()
        logger.info("Begin set up of challenge.")

        http_port = 44000
        openvpn_port = 45000
        challenge_counter = 1
        next_network = self.subnet

        ports_in_use = []
        for idx, user in enumerate(self.config.get("users")):
            if os.path.exists(f"{self.save_path}/data/{user}"):
                logger.info(f"Check ports for user: {user}")
                ip, existing_openvpn_port = self._extract_ovpn_info(
                    f"{self.save_path}/data/{user}/client.ovpn"
                )
                ports_in_use.append(existing_openvpn_port)

                host: Host = [d for d in self.hosts if str(d.ip) == ip][0]
                con = host.get_container(user, "openvpn")
                if con != None:
                    logger.debug(f"Container: {con.name}")
                    if con.ports:
                        for port, bindings in con.ports.items():
                            logger.debug(f"  Port {port}:")
                            for binding in bindings:
                                logger.debug(f"    - Host IP: {binding['HostIp']}, Host Port: {binding['HostPort']}")
                                ports_in_use.append(binding['HostPort'])
                    else:
                        logger.debug("  No ports allocated.")


        logger.info(f"Ports in use: {ports_in_use}")

        for idx, user in enumerate(self.config.get("users")):
            in_use = True
            while in_use:
                if (not (str(openvpn_port + challenge_counter)) in ports_in_use) and (not (str(http_port + challenge_counter)) in ports_in_use):
                    in_use = False
                else:
                    challenge_counter += 1

            if os.path.exists(f"{self.save_path}/data/{user}"):
                logger.info(f"OpenVPN data exists for the user: {user}")
                logger.info(
                    f"Data for the user: {user} will NOT be changed. Starting OVPN Docker container with existing data."
                )
                
                # TODO Extract subnet
                ip, existing_openvpn_port = self._extract_ovpn_info(
                    f"{self.save_path}/data/{user}/client.ovpn"
                )

                host: Host = [d for d in self.hosts if str(d.ip) == ip][0]
                logger.info(f"Deploy on host: {host.ip}")


                if not self._check_running(user=user, host=host):

                    host.send_and_extract_tar(user=user)

                    host.start_openvpn(
                        user=user,
                        openvpn_port=existing_openvpn_port,
                        http_port=http_port + challenge_counter,
                        subnet=next_network,
                    )

                    self._start_containers(host=host, subnet=next_network, user=user)
            else:
                logger.info(
                    f"For the user: {user}, an OpenVPN configuration file will be generated!"
                )
                host: Host = self.hosts[-1]
                host: Host = self.hosts[idx % len(self.hosts)]
                # logger.info(f"Deploy on host: {host.ip}")

                if not self._check_running(user=user, host=host):
                    
                    host.start_openvpn(
                        user=user,
                        openvpn_port=openvpn_port + challenge_counter,
                        http_port=http_port + challenge_counter,
                        subnet=next_network,
                    )

                    self._start_containers(host=host, subnet=next_network, user=user)


            next_network = ip_network(
                (int(next_network.network_address) + next_network.num_addresses),
                strict=False,
            )
            next_network = next_network.supernet(new_prefix=24)
            challenge_counter += 1

    def _start_containers(self, user: str, host: Host, subnet: IPv4Network | IPv6Network):
        used_ip = []
        for container in self.config.get("containers"):
            used = True
            while used:
                random_ip = random.randint(3, 254)
                if not random_ip in used_ip:
                    used_ip.append(random_ip)
                    used = False
            logger.info(f"Randomized port {random_ip}")
            host.start_container(
                user=user, container=container, subnet=subnet, index=random_ip, environment={
                    "USER": user,
                    "SECRET": self.config.get("secret")
                }
            )

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
@click.option(
    "--prune",
    default=False,
    is_flag=True,
    help="Prunes all running containers on the host machine.",
    show_default=True,
)
def main(config, save, prune):
    ctfcreator = CTFCreator(config=config.read(), save_path=save, prune=prune)
    ctfcreator.create_challenge()


if __name__ == "__main__":
    main()
