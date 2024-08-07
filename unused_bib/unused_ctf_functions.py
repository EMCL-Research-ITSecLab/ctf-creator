# Example to create a Jump Host but it it currently not used!
#doc.create_jump_host(docker_client,network_name,user_name,f"{subnet_first_part[0]}.{subnet_second_part[0]}.{subnet_base}.2",k,hosts[current_vm-1])

#!!! Bug in create split VPN test it does not chang the other server conf it a different folder!
#doc.create_split_vpn_on_host(docker_client,user_name,new_push_route,save_path,k)

#!!! To mount the data correctly need to send the data to the host!!! make sure it funtionkioert bugfree
        #!!! better send a python script per ssh and start it?!
        #!!! change the mount folder in start ovpn with old data!
        #hosts_func.execute_ssh_command(hosts[current_vm-1],"mkdir download_dockovpn_data")
        #hosts_func.send_tar_file_via_ssh(f"{save_path}/data/{user_name}/dockovpn_data.tar",hosts[current_vm-1],"/home/ubuntu/download_dockovpn_data/dockovpn_data.tar")
        #hosts_func.execute_ssh_command(hosts[current_vm-1],"tar -xvf /home/ubuntu/download_dockovpn_data/dockovpn_data.tar -f")
        #hosts_func.execute_ssh_command(hosts[current_vm-1],f"sudo rm -r ctf-data" )
        #hosts_func.send_and_extract_tar_via_ssh_v2(f"{save_path}/data/{user_name}/dockovpn_data.tar",extracted_hosts_username[current_vm-1],extracted_hosts[current_vm-1],f"/home/{extracted_hosts_username[current_vm-1]}/ctf-data/{user_name}/dock_vpn_data.tar")
        # !!! current bug 5.08 need to change the save or remote path!!!
        #doc.create_openvpn_server_with_existing_data(docker_client,network_name,user_name,f"{subnet_first_part[0]}.{subnet_second_part[0]}.{subnet_base}.2",k, current_host,f"/home/{extracted_hosts_username[current_vm-1]}/ctf-data/{user_name}/Dockovpn_data/")
        # !!! Start the docker container. and push the old configs to the right place and then docker restart. 
        #doc.upload_existing_openvpn_config(docker_client,save_path,user_name)
        # 
        #click.echo(f"For {user_name } the OVPN Docker container is running and can be connected with the the existing data")

# !!! Start the docker container. and push the old configs to the right place and then docker restart. 
        #doc.upload_existing_openvpn_config(docker_client,save_path,user_name)
        # 
        #click.echo(f"For {user_name } the OVPN Docker container is running and can be connected with the the existing data")
      #