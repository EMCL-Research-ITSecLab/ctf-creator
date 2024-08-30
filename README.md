# CTF-Creator

The main function of the CTF-Creator aims to automate the setup of a CTF environment by managing Docker containers, networking, and security configurations. It streamlines the process of provisioning resources for multiple users, ensuring each participant has a dedicated and secure environment tailored to the CTF requirements and creating OVPN files for a secure connection with the CTF environment.

By integrating with Docker, SSH, and networking tools, the main function facilitates the creation of isolated environments where participants can engage in challenges, exercises, or simulations typical of Capture The Flag competitions. This automation not only saves time but also enhances the scalability and consistency of CTF environments across different hosts and setups.

## Folders and Files

The project consists of three folders:
1. **src**: Where all relevant files and scripts are:
    - `ctf_main.py`
    - `docker_functions.py`
    - `pyyaml_functions.py`
    - `tar_functions.py`
    - `ovpn_helper_functions.py`
2. **unused_bib**: A folder where all functions are stored which were used at some point during development but are no longer necessary:
    - `ssh_functions.py`
    - `zip_functions.py`
3. **data**: Example folder with the user data the CTF-Creator generates to connect to the CTF environment. Each user has their own folder named `user_user_name` containing a `client.zip` with OVPN configuration for the connection with the secure environment and other backup data for the connection.

## Installation Instructions

Python 3 needs to be installed.

**Recommendation**: Before running `ctf_main.py`, create a Python virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
```
## Usage 
Provide a YAML configuration file with the following arguments:

    name: Name of the YAML configuration.
    containers: Docker containers that get started for each user.
    users: List of users.
    identityFile: Path to the private SSH key for host login.
    hosts: Hosts where the Docker containers are running.
    subnet_first_part: IP address, formatted as first_part.xx.xx.xx/24.
    subnet_second_part: IP address, formatted as xx.second_part.xx.xx/24.
    subnet_third_part: IP address, formatted as xx.xx.third_part.xx/24.
    wireguard_config: Name of your WireGuard configuration needed to connect to the hosts.

Run ctf_main.py with Python 3 in the src folder.

Provide the location of your YAML configuration file and where you want to store the created data for the connection to the CTF environment.

For connecting to the hosts, it will also ask for your terminal password.
## Features

#### Main Function Overview

The main function orchestrates the entire setup process for the CTF-Creator, leveraging various helper functions and external libraries like Docker, Paramiko (SSH), and Click (command-line interface).
Key Functionalities:

    Loading Configuration:
        Reads and parses a YAML configuration file (config.yaml) that defines:
            Docker containers to be started for each user.
            Users participating in the CTF.
            Paths to SSH keys, WireGuard configurations, and other network details.
            Hosts where Docker containers will run.
            IP address subnets for network configuration.

    Establishing Connections:
        Sets up SSH connections using Paramiko and WireGuard connections as defined in the configuration.
        Manages SSH agent for key-based authentication during operations.

    Network and Container Management:
        Cleans up existing Docker containers and networks on specified hosts to ensure a clean state.
        Creates Docker networks for each user, ensuring isolated environments for containers.
        Deploys specified Docker containers for each user within their respective networks.

    Security and Configuration:
        Handles security configurations like setting up WireGuard VPN for secure connections to Docker hosts.
        Manages user-specific OpenVPN servers and configuration files for secure client-server communication within the CTF environment.

    Error Handling and Retry Mechanism:
        Implements error handling and retry mechanisms (via max_retries parameter) for critical operations like file downloads (using curl) and configuration modifications.
        Ensures robustness and reliability during setup and configuration phases.

    Output and Logging:
        Provides informative messages using click.echo to keep users informed about the progress and status of operations.
        Logs errors and exceptions to aid in debugging and troubleshooting.

## Credits

This is the CTF-Creator programmed by Nick Nötzel under the supervision of Stefan Machmeier.
## License
EUROPEAN UNION PUBLIC LICENCE. Take a look at the LICENSE.md

