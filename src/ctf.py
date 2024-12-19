import os
import random
import sys
from typing import List
from docker import DockerClient
import yamale
import click
import pathlib
import sys
import os
import time

from subprocess import run, CalledProcessError
from docker import DockerClient
from docker.errors import NotFound

from ipaddress import IPv4Network, IPv6Network, ip_network
from yamale import YamaleError
from yamale.validators import DefaultValidators
from docker.errors import NotFound, APIError

sys.path.append(os.getcwd())
from src.host import Host
from src.log_config import get_logger
from src.utils import Path
from src.participant import Participant
from src.gen_flag import gen_flag


logger = get_logger("ctf_creator.ctf")


class DownloadError(Exception):
    """Custom exception for download errors."""

    pass


class RemoteLineNotFoundError(Exception):
    """Custom exception raised when no 'remote' line is found in the OpenVPN configuration file."""

    pass


class CTFCreator:
    def __init__(self, config: str, save_path: str, prune: bool, kalibox: bool, recreate: bool) -> None:
        self.config = self._get_config(config)
        self.prune = prune
        self.kalibox = kalibox
        self.recreate = recreate
        self.openvpn_port = 45000
        self.challenge_counter = 1
        
        logger.info(f"Containers: {self.config.get('containers')}")
        logger.info(f"Users: {self.config.get('users')}")
        logger.info(f"Key: {self.config.get('key')}")
        logger.info(f"Hosts: {self.config.get('hosts')}")
        logger.info(f"IP-Address Subnet-base: {self.config.get('subnet')}")

        self.total_amount = len(self.config.get("containers")) + 1
        if self.kalibox:
            self.total_amount = self.total_amount + 1
        logger.info(f"Total number of containers per user {self.total_amount}")

        self.save_path = save_path
        self.subnet = ip_network(self.config.get("subnet"))
        self.next_network = self.subnet

        self.local_docker = DockerClient(base_url="unix:///var/run/docker.sock")
        self.local_docker_ip = "0.0.0.0"
        self.local_docker_port = "85"
        self.local_docker_openvpn = "local_vpn"

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

    def _start_local_openvpn(self):
        try:
            con = self.local_docker.containers.get(self.local_docker_openvpn)
            if con:
                return
        except NotFound:
            logger.warning(f"Not started yet.")

        try:
            container = self.local_docker.containers.run(
                image="alekslitvinenk/openvpn",
                detach=True,
                name=self.local_docker_openvpn,
                command="-s",
                restart_policy={"Name": "always"},
                cap_add=["NET_ADMIN"],
                ports={"8080/tcp": str(self.local_docker_port)},
                healthcheck={
                    "test": ["CMD-SHELL", f"netstat -lun | grep -c 1194"],
                    "interval": 1000000,
                    "retries": 5,
                },
                mem_limit="256m",
                memswap_limit=0,
                cpu_quota=100000,
            )

            return container
        except APIError as e:
            logger.error(f"Error creating container: {e}")
            raise

    def _stop_local_openvpn(self):
        con = self.local_docker.containers.get(self.local_docker_openvpn)
        if con:
            con.stop()
            con.remove()

    def _curl_client_ovpn(
        self,
        user: str,
        save_path: str,
        max_retries_counter=0,
        max_retries=25,
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
        url = f"http://{self.local_docker_ip}:{self.local_docker_port}/client.ovpn"

        try:
            os.makedirs(save_directory, exist_ok=True)
            command = f"curl -o {save_directory}/client.ovpn {url}"

            while max_retries_counter < max_retries:
                try:
                    run(command, shell=True, check=True)
                    logger.info(
                        f"File downloaded successfully to {save_directory}/client.ovpn"
                    )
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

    def _openvpn_config(self, user: Participant):
        logger.info(f"Downloading OpenVPN configuration for {user.name}...")

        # Download the folder with data
        try:
            container = self.local_docker.containers.get(self.local_docker_openvpn)
        except NotFound:
            logger.error(f"Error: Container {self.local_docker_openvpn} not found.")
            exit(1)
        except Exception as e:
            logger.error(
                f"Error: Something is wrong with {self.local_docker_openvpn}. {e}"
            )
            exit(1)

        unhealthy = True
        max_retries = 0
        while unhealthy or max_retries == 25:
            container = self.local_docker.containers.get(self.local_docker_openvpn)
            if container.attrs["State"]["Health"]:
                health_status = container.attrs["State"]["Health"]["Status"]
                logger.info(
                    f"{self.local_docker_openvpn}: Health status: {health_status}"
                )
                if health_status == "healthy":
                    unhealthy = False
            else:
                logger.info(
                    f"{self.local_docker_openvpn}: No healthcheck defined for this container"
                )
            max_retries += 1
            time.sleep(5)

        try:
            logger.info("Executing command in container...")
            _, _ = container.exec_run("./genclient.sh", detach=True)
            # Delay to give time to run the command in the container
            time.sleep(5)
            self._curl_client_ovpn(user=user.name, save_path=user.save_path)
        except Exception as e:
            logger.error(f"Error: Unable to execute command in container. {e}")
            exit(1)

        try:
            container = self.local_docker.containers.get(self.local_docker_openvpn)
            local_save_path = f"{user.save_path}/data/{user.name}"
            local_path_to_data = f"{user.save_path}/data/{user.name}/dockovpn_data.tar"
            os.makedirs(local_save_path, exist_ok=True)
            archive, _ = container.get_archive("/opt/Dockovpn_data")
            # Save the archive to a local file
            with open(local_path_to_data, "wb") as f:
                for chunk in archive:
                    f.write(chunk)
            logger.info(f"Container found: {self.local_docker_openvpn}")
            logger.info("And the Dockovpn_data folder is saved on this system")
        except NotFound:
            logger.info(f"Error: Container {self.local_docker_openvpn} not found.")
            exit(1)
        except Exception as e:
            logger.info(
                f"Error: Something is wrong with the saving of the ovpn_data!. {e}"
            )
            exit(1)

    def _modify_ovpn_client(self, user: Participant) -> None:
        """
        Changes the IP address and port in the 'remote' line of an OpenVPN configuration file
        only if the IP address or port is different from the current values.

        Args:
            user (str): Username associated with the OpenVPN configuration file.
            port (int): New port number to replace in the 'remote' line.

        Returns:
            str: The username if the configuration was changed, otherwise None.
        """
        if not os.path.exists(f"{user.save_path}/data/{user.name}/client.ovpn"):
            logger.info(
                f"File {f'{user.save_path}/data/{user.name}/client.ovpn'} does not exist."
            )
            return None

        modified_lines = []

        with open(f"{user.save_path}/data/{user.name}/client.ovpn", "r") as file:
            lines = file.readlines()

        remote_line_found = False
        change_needed = False

        for line in lines:
            if line.startswith("remote "):
                parts = line.split()
                if len(parts) == 3:
                    current_ip = parts[1]
                    current_port = parts[2]

                    if current_ip != user.ip or current_port != str(
                        user.existing_openvpn_port
                    ):
                        parts[1] = str(user.ip)
                        parts[2] = str(user.existing_openvpn_port)
                        line = " ".join(parts) + "\n"
                        change_needed = True

                    remote_line_found = True

            modified_lines.append(line)

        if not remote_line_found:
            raise RemoteLineNotFoundError("No 'remote' line found in the file.")

        if change_needed:
            with open(f"{user.save_path}/data/{user.name}/client.ovpn", "w") as file:
                file.writelines(modified_lines)
            logger.info(
                f"IP address and port in the 'remote' line of {f'{user.save_path}/data/{user.name}/client.ovpn'} have been successfully modified."
            )
        else:
            logger.info(
                f"No change needed for {user}. The IP address and port are already correct."
            )

    def _check_running(self, user: str, host: Host):
        logger.info("Check if containers and OpenVPN exists...")

        running = []

        if host.container_exists(user=user, container="openvpn"):
            running.append("openvpn")

        if self.kalibox and host.container_exists(user=user, container="kali"):
            running.append("kali")

        if len(running) == self.total_amount:
            logger.info(f"All are up and running for {user}")
        else:
            logger.info(f"Remove containers, not all are up and running for {user}")

            if self.recreate:
                logger.debug("Remove OpenVPN container to recreate.")
                host.container_remove(user=user, container="openvpn")
                if "openvpn" in running:
                    running.remove("openvpn")

            if self.kalibox and self.recreate:
                logger.debug("Remove Kalibox container to recreate.")
                host.container_remove(user=user, container="kali")
                if "kali" in running:
                    running.remove("kali")

            host.challenge_remove(user=user)
            
            if self.recreate:
                host.network_remove(user=user)

            return running

    def create_challenge(self):
        logger.info("Set up hosts.")
        self.hosts = self._get_hosts()
        logger.info("Begin set up of challenge.")

        used_ports = []
        used_subnets = []
        users = []
        logger.info("\u2500" * 120)
        for idx, mail in enumerate(self.config.get("users")):
            user_obj = Participant(user=mail, save_path=self.save_path)

            if os.path.exists(f"{user_obj.save_path}/data/{user_obj.name}"):
                logger.info(f"OpenVPN data exists for the user: {user_obj.name}")
                logger.debug(
                    f"Data for the user: {user_obj.name} will NOT be changed. Starting OVPN Docker container with existing data."
                )
                used_ports.append(int(user_obj.existing_openvpn_port))
                used_subnets.append(str(user_obj.subnet))

            users.append(user_obj)

        logger.info(f"Ports in use {used_ports}")
        logger.info(f"Subnets in use {used_subnets}")
        logger.info("\u2500" * 120)
        
        futures = []
        for idx, user in enumerate(users):
            if not os.path.exists(f"{self.save_path}/data/{user.name}"):
                self._create_openvpn_data(idx, user, used_ports, used_subnets)

            host: Host = [d for d in self.hosts if str(d.ip) == str(user.ip)][0]
            logger.debug(f"Deploy on host: {host.ip}")

            self.deploy_challenge(user, host)
    
    def deploy_challenge(self, user: Participant, host: Host) -> str:

        logger.info("\u2500" * 120)
        logger.info(f"Create Challenge for {user.name}")

        running = self._check_running(user=user.name, host=host)

        if not "openvpn" in running:
            host.send_and_extract_tar(user=user.name)
            # TODO fix problem, that OpenVPN creates the network
            host.start_openvpn(
                user=user.name,
                openvpn_port=user.existing_openvpn_port,
                subnet=user.subnet,
            )

        self._start_containers(host=host, subnet=user.subnet, user=user.name)

        if self.kalibox and not "kali" in running:
            self._start_kalibox(user=user.name, host=host, subnet=user.subnet)

        logger.info("\u2500" * 120)

        return f"Done for User: {user.name}"
    
    def _create_openvpn_data(self, idx:int, user: Participant, used_ports: list, used_subnets: list):
        logger.info(
            f"For the user: {user.name}, an OpenVPN configuration file will be generated!"
        )
        host: Host = self.hosts[idx % len(self.hosts)]
        user.ip = host.ip
        # Get free port
        in_use = True
        while in_use:
            if not (self.openvpn_port + self.challenge_counter) in used_ports:
                in_use = False
            else:
                self.challenge_counter += 1
        user.existing_openvpn_port = self.openvpn_port + self.challenge_counter
        used_ports.append(self.openvpn_port + self.challenge_counter)
        # Get free subnet
        in_use = True
        while in_use:
            if not str(self.next_network) in used_subnets:
                in_use = False
            else:
                self.next_network = ip_network(
                    (
                        int(self.next_network.network_address)
                        + self.next_network.num_addresses
                    ),
                    strict=False,
                )
                self.next_network = self.next_network.supernet(new_prefix=24)
        user.subnet = self.next_network
        used_subnets.append(str(self.next_network))

        logger.debug(f"Deploy on host: {host.ip}")

        self._start_local_openvpn()
        self._openvpn_config(user=user)
        self._modify_ovpn_client(user=user)
        self._stop_local_openvpn()
        user.write_readme()

    def _start_containers(
        self, user: str, host: Host, subnet: IPv4Network | IPv6Network
    ):
        used_ip = []
        for container in self.config.get("containers"):
            used = True
            while used:
                random_ip = random.randint(4, 254)
                if not random_ip in used_ip:
                    used_ip.append(random_ip)
                    used = False
            logger.debug(f"Randomized port {random_ip}")
            host.start_container(
                user=user,
                container=container,
                subnet=subnet,
                index=random_ip,
                environment={"USER": user, "SECRET": self.config.get("secret"), "FLAG": gen_flag(secret=self.config.get("secret"), user=f"{user}_{container['name']}")},
            )

    def _start_kalibox(self, user: str, host: Host, subnet: IPv4Network | IPv6Network):
        logger.info(f"Start kalibox on {str(subnet.network_address + 3)}")
        host.start_kali(
            user=user,
            subnet=subnet,
            index=3,
            command=[self.config.get("secret"), "kali"],
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
@click.option(
    "--kali",
    default=False,
    is_flag=True,
    help="Provides a Kali Docker container for network tracing.",
    show_default=True,
)
@click.option(
    "--recreate",
    default=False,
    is_flag=True,
    help="Provides a Kali Docker container for network tracing.",
    show_default=True,
)
def main(config, save, prune, kali, recreate):
    ctfcreator = CTFCreator(config=config.read(), save_path=save, prune=prune, kalibox=kali, recreate=recreate)
    ctfcreator.create_challenge()


if __name__ == "__main__":
    main()
