<a id="readme-top"></a>

<!-- PROJECT SHIELDS -->
<div align="center">

[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![EUPL License][license-shield]][license-url]

</div>

# CTF-Creator

The Capture-The-Flag (CTF)-Creator is a Python-based project designed to automate the setup of CTF environments by managing Docker containers, networking, and security configurations. It simplifies the process of provisioning resources for multiple users, ensuring each participant has a dedicated and secure environment tailored to specific CTF requirements, as well as creating OpenVPN configuration files for secure connections to the CTF environment.

By integrating with Docker, SSH, and networking tools, the system automates the creation of isolated environments that include the necessary Docker containers responsible for the CTF setup. Once participants are connected to their respective environments, they can engage in challenges, exercises, or simulations typical of CTF competitions. This automation not only saves time but also enhances the scalability and consistency of CTF environments across different hosts and setups.

# Getting Started

## Installation Instructions

Python 3 and several Python libraries need to be installed. They can be installed with
```bash
pip install -r requirements.txt
```

**Recommendation**: Before running `ctf_main.py`, create a Python virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
```
## Requirements

### Input requirements

An example YAML config file named `challenge.yaml` is available in the root directory to illustrate the required structure.

```sh
$ python3 src/ctf.py
Usage: ctf.py [OPTIONS]

Options:
  --config FILENAME  The path to the .yaml configuration file for the CTF-
                     Creator.  [required]
  --save PATH        The path where you want to save the user data for the
                     CTF-Creator. E.g. /home/debian/ctf-creator  [required]
  --prune            Prunes all running containers on the host machine.
  --help             Show this message and exit.
```

Sufficient memory space and the necessary system permissions are required to save the configuration files for each CTF environment user on the system running the CTF-Creator. The amount of space needed will depend on the number of users in the CTF environment, with an estimated space requirement of 140 KB per user.

### Requirements for the remote hosts that are specified in the YAML configuration
**The hosts need to be capable of spawning Docker containers. For that please follow the instructions**:

1. You need to install [Docker](https://docs.docker.com/engine/install/ubuntu/)

2. You need to configure [remote access Docker daemon](https://docs.docker.com/engine/daemon/remote-access/)

3. You need to be able to use Docker without privilaged Access run follwoing comand in the terminal of the remote hosts

```sh
sudo usermod -aG docker $(whoami) && newgrp docker
```

The hosts need to support SSH connections using asymmetric public and private keys for secure remote access.
Verify that `ssh-agent` is running

```sh
eval "$(ssh-agent)"
```

Add SSH keys to agent:

```sh
ssh-add /path/to/identity
```

### Use Cases

1. Fresh set up: Creating the Environment Without Reusing OVPN Data
2. Reusing Existing OVPN Configurations Without Adding New Users:
3. Reusing Existing OVPN Configurations While Adding New Users
4. Reusing Data While Modifying Hosts

For use case 1 specify a save path with no existing data created by the CTF-Creator.
For the use cases 2-4 specify a save path where user data already exists.

For every use case, the list of deploying Docker containers can be changed.

For any other use case scenario please start a fresh set up.

## Testing

To run all tests at once you can run this command in the terminal in the main folder `ctf-creator/`:

```sh
python3 -m pytest -v
```
## Credits

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

### Top contributors:

<a href="https://github.com/EMCL-Research-ITSecLab/ctf-creator/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=EMCL-Research-ITSecLab/ctf-creator" alt="contrib.rocks image" />
</a>


## License
[EUPL](https://joinup.ec.europa.eu/sites/default/files/custom-page/attachment/2020-03/EUPL-1.2%20EN.txt)


<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/EMCL-Research-ITSecLab/ctf-creator.svg?style=for-the-badge
[contributors-url]: https://github.com/EMCL-Research-ITSecLab/ctf-creator/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/EMCL-Research-ITSecLab/ctf-creator.svg?style=for-the-badge
[forks-url]: https://github.com/EMCL-Research-ITSecLab/ctf-creator/network/members
[stars-shield]: https://img.shields.io/github/stars/EMCL-Research-ITSecLab/ctf-creator.svg?style=for-the-badge
[stars-url]: https://github.com/EMCL-Research-ITSecLab/ctf-creator/stargazers
[issues-shield]: https://img.shields.io/github/issues/EMCL-Research-ITSecLab/ctf-creator.svg?style=for-the-badge
[issues-url]: https://github.com/EMCL-Research-ITSecLab/ctf-creator/issues
[license-shield]: https://img.shields.io/github/license/EMCL-Research-ITSecLab/ctf-creator.svg?style=for-the-badge
[license-url]: https://github.com/EMCL-Research-ITSecLab/ctf-creator/blob/master/LICENSE.txt
[coverage-shield]: https://img.shields.io/codecov/c/github/EMCL-Research-ITSecLab/ctf-creator?style=for-the-badge
[coverage-url]: https://app.codecov.io/github/EMCL-Research-ITSecLab/ctf-creator
