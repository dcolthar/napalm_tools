import netmiko

def enable_scp_server(host, username, password, device_type):
    # remap device type for netmiko
    if device_type == 'ios':
        device_type = 'cisco_ios'

    # command set
    cmd_set = ['ip scp server enable']

    # set up connection
    endpoint = {
            'host': host,
            'username': username,
            'password': password,
            'device_type': device_type
        }
    connection = netmiko.ConnectHandler(**endpoint)
    # send the commands
    connection.send_config_set(cmd_set)
    # disconnect
    connection.disconnect()

def check_scp_server(network_connection):
    # command to use to check
    show_run_scp_server = 'show run | include ip scp server'
    # run the command
    result = network_connection.cli([show_run_scp_server])
    # return true/false
    if result['show run | include ip scp server']:
        return True
    else:
        return False