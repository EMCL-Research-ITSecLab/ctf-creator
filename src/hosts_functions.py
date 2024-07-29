import subprocess
import sys

def check_host_reachability_with_ping(host_ips):
    unreachable_hosts = []
    
    for host in host_ips:
        try:
            result = subprocess.run(['ping', '-c', '1', host], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode != 0:
                unreachable_hosts.append(host)
        except Exception as e:
            print(f"Error pinging host {host}: {e}")
            unreachable_hosts.append(host)
    
    if unreachable_hosts:
        print("The following hosts are unreachable:")
        for host in unreachable_hosts:
            print(f"- {host}")
        print("Please check if you are connected to the correct WireGuard VPN to ensure connectivity with these hosts.")
        sys.exit(1)
    else:
        print("All hosts are reachable with ping.")


def check_ssh_connection(host_info):
    try:
        # Attempt to SSH into the host
        result = subprocess.run(
            ['ssh', host_info, 'exit'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            if "Permission denied" in result.stderr:
                print(f"SSH connection to {host_info} failed due to incorrect username or password.")
            else:
                print(f"SSH connection to {host_info} failed: {result.stderr}")
            return False
        return True
    except subprocess.TimeoutExpired:
        print(f"SSH connection to {host_info} timed out.")
        return False
    except Exception as e:
        print(f"Error attempting SSH connection to {host_info}: {e}")
        return False
    

#Uses also the unsername so you can deduce if the host Ip is wrong or the username!
def check_host_reachability_with_SSH(host_infos):
    unreachable_hosts = []

    for host_info in host_infos:
        if not check_ssh_connection(host_info):
            unreachable_hosts.append(host_info)
    
    if unreachable_hosts:
        print("The following hosts are unreachable or have incorrect SSH credentials:")
        for host_info in unreachable_hosts:
            print(f"- {host_info}")
        print("Please check if you are connected to the correct WireGuard VPN and using the correct SSH host-username.")
        sys.exit(1)
    else:
        print("All SSH connections to hosts were successful.")
