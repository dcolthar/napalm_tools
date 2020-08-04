# get and write the full config to a file
from napalm import get_network_driver
import json

def get_full_config(network_connection, hostname):
    '''
    Get the full config and write to a file named after the host
    :param network_connection:
    :param hostname:
    :return:
    '''
    base_folder = 'config_output'
    # get config
    try:
        full_config = network_connection.get_config()
        # write the config
        full_filename = f'{base_folder}/{hostname}_config.txt'
        with open(full_filename, 'w') as f:
            f.write(full_config['startup'])
    except Exception as e:
        print(f'error occurred obtaining or writing the config for host {hostname}\n{e}')