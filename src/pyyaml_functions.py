"""
This module provides functionalities for the CTF-Creator,
including reading and validating configuration data from a YAML file,
and extracting relevant information for setting up Docker containers and network configurations.

The main functionalities include:

1. Validating required fields in the YAML configuration.
2. Extracting and returning relevant data for setting up Docker containers.
3. Reading a WireGuard configuration from a YAML file.
4. Extracting host information from provided data.

Functions:
- read_yaml_data(file_path): Reads and validates configuration data from a YAML file.
- extract_hosts(hosts): Extracts the host part from each string in a list of hosts.
"""
import yaml
import click



def read_data_from_yaml(data):
 
    required_fields = ['containers', 'users', 'identityFile', 'hosts', 'wireguard_config', 
                       'subnet_first_part', 'subnet_second_part', 'subnet_third_part']
    
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing {field} field in YAML data")

    # Store containers and users in separate lists
    containers = data.get('containers', [])
    users = data.get('users', [])
    key = data.get('identityFile', [])
    hosts = data.get('hosts' ,[])
    wireguard_config = data.get('wireguard_config' ,[])
    #subnet_begin = data.get('subnet_begin' ,[])
    subnet_first_part = data.get('subnet_first_part' ,[])
    subnet_second_part = data.get('subnet_second_part' ,[])
    subnet_third_part = data.get('subnet_third_part' ,[])
  
    
    return containers, users, key, hosts, wireguard_config,subnet_first_part, subnet_second_part, subnet_third_part


def read_yaml_data(file_path):
    """
    Reads configuration data from a YAML file and validates the required fields.

    Args:
        file_path (str): Path to the YAML file to read.

    Returns:
        tuple: A tuple containing the following:
            - containers (list): List of Docker containers to be started for each user.
            - users (list): List of users.
            - key (str): Path to the private SSH key for host login.
            - hosts (list): List of hosts where the Docker containers are running.
            - wireguard_config (str): Name of the WireGuard configuration.
            - subnet_first_part (str): IP address, formatted as firstpart.xx.xx.xx/24.
            - subnet_second_part (str): IP address, formatted as xx.second_part.xx.xx/24.
            - subnet_third_part (str): IP address, formatted as xx.xx.third_part.xx/24.

    Raises:
        ValueError: If any of the required fields are missing in the YAML data.
    """
    with open(file_path, 'r') as file:
        data = yaml.safe_load(file)
    
    
    required_fields = ['containers', 'users', 'identityFile', 'hosts', 'wireguard_config', 
                       'subnet_first_part', 'subnet_second_part', 'subnet_third_part']
    
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing {field} field in YAML data")

    # Store containers and users in separate lists
    containers = data.get('containers', [])
    users = data.get('users', [])
    key = data.get('identityFile', [])
    hosts = data.get('hosts' ,[])
    wireguard_config = data.get('wireguard_config' ,[])
    #subnet_begin = data.get('subnet_begin' ,[])
    subnet_first_part = data.get('subnet_first_part' ,[])
    subnet_second_part = data.get('subnet_second_part' ,[])
    subnet_third_part = data.get('subnet_third_part' ,[])
  
    
    return containers, users, key, hosts, wireguard_config,subnet_first_part, subnet_second_part, subnet_third_part


# Function to extract the host part from each string
def extract_hosts(hosts):
    """
    Extracts the host part from each string in a list of hosts.

    Args:
        hosts (list): List of host strings, each containing an '@' symbol.

    Returns:
        list: A list of extracted host parts. If a host string does not contain an '@' symbol, None is returned for that entry.
    """
    extracted_hosts = []
    for host in hosts:
        try:
            extracted_host = host.split('@')[1]
            extracted_hosts.append(extracted_host)
        except IndexError:
            # Handle the case where there is no '@' symbol in the string
            extracted_hosts.append(None)
    return extracted_hosts

@click.command()
@click.option('--config', prompt='Please enter the path to your .yaml file', help='The path to the .yaml configuration file for the ctf-creator.')
def load_config_and_read(config):
    """Load and process the YAML configuration file for ctf-creator."""
    try:
        containers, users, key, hosts, wireguard_config, subnet_first_part, subnet_second_part, subnet_third_part = read_yaml_data(config)
        click.echo('YAML file loaded successfully.')
        # Process the YAML data as needed for the ctf-creator
        click.echo(f"Containers: {containers}")
        click.echo(f"Users: {users}")
        click.echo(f"Key: {key}")
        click.echo(f"Hosts: {hosts}")
        click.echo(f"WireGuard Config: {wireguard_config}")
        click.echo(f"Subnet First Part: {subnet_first_part}")
        click.echo(f"Subnet Second Part: {subnet_second_part}")
        click.echo(f"Subnet Third Part: {subnet_third_part}")
        return containers, users, key, hosts, wireguard_config, subnet_first_part, subnet_second_part, subnet_third_part
    except FileNotFoundError:
        click.echo('Error: The specified file was not found.')
    except yaml.YAMLError as exc:
        click.echo(f'Error parsing YAML file: {exc}')
    except Exception as e:
        click.echo(f'An unexpected error occurred: {e}')

@click.command()
@click.option('--config', prompt='Please enter the path to your .yaml file', help='The path to the .yaml configuration file for the ctf-creator.')
def load_config(config):
    """Load and process the YAML configuration file for ctf-creator."""
    try:
        with open(config, 'r') as file:
            data = yaml.safe_load(file)
            click.echo('YAML file loaded successfully.')
            # Process the YAML data as needed for the ctf-creator
            #click.echo(data)
            return data
    except FileNotFoundError:
        click.echo('Error: The specified file was not found.')
    except yaml.YAMLError as exc:
        click.echo(f'Error parsing YAML file: {exc}')
    except Exception as e:
        click.echo(f'An unexpected error occurred: {e}')