import docker_functions as doc 
#import ssh_functions as ssh
#import zip_functions as zip
#import docker
#import os
#import pyyaml_functions as yaml
import subprocess



# Get the last number from the user
last_number = int(input("Which host? Enter 1-4 "))

# Define ssh-agent commands as a list
commands = [
    f'ssh -i /home/nick/Data/ssh_key ubuntu@10.20.30.10{last_number}'
  ]

  # Execute each commands in the list
for command in commands:
    subprocess.run(command, shell=True)
