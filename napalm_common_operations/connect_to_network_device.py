import napalm

def connect_to_network_device(host, username, password, device_type):
    # convert device types if needed
    if device_type == 'cisco_ios':
        device_type = 'ios'
    elif device_type == 'cisco_nxos':
        device_type = 'nxos_ssh'
    # configure the network driver
    driver = napalm.get_network_driver(device_type)
    # connect to the device
    try:
        network_connection = driver(host, username, password)
        network_connection.open()
        # return the network connection
        return network_connection
    except Exception as e:
        print(f'An error occurred connecting to the host {host}\n{e}')
        return False

def disconnect_from_network_device(network_connection):
    # just disconnect
    network_connection.close()