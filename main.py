import napalm_common_operations
from getpass import getpass
import threading
from queue import Queue
import pandas as pd
import argparse
import os



class Main():

    def __init__(self):
        args = argparse.ArgumentParser()
        args.add_argument('--get_config', help='will copy the full config to the config_output folder',
                          action='store_true')
        ### legacy tacacs conversion works but want to add in something to prompt prior to changes for each unit and
        ### to show the changes being made ahead of the actual change
        args.add_argument('--tacacs_legacy_upgrade', help='will convert any legacy tacacs config to new format',
                          action='store_true')
        ### Work in progress as well to check ospf neighbor health on links
        args.add_argument('--check_ospf_link_health', help='any interface with ospf neighbor, check health',
                          action='store_true')
        args.add_argument('--interface_uptime_check',
                          help='create a report of interfaces and last time passed traffic on the links ',
                          action='store_true')
        args.add_argument('--port_mapping', help='build out logical info for a port mapping and write to excel',
                          action='store_true')
        args.add_argument('--file_name', help='name of the file to pull hosts from default is host_list.xlsx',
                          default='host_list.xlsx')
        args.add_argument('--port_mapping_output_file',
                          help='name of output file to write port mapping to, default is port_mapping_output.xlsx',
                          default='port_mapping_output.xlsx')
        args.add_argument('--image_filename', help='port mapping report image file, default is generic_company_logo.jpg',
                          default='images/generic_company_logo.jpg')
        args.add_argument('--thread_max', help='number of worker threads to concurrently run default is 5', default=5),
        args.add_argument('--username', help='the username to use to connect to devices', default='admin')
        # parse all the arguments
        arguments = args.parse_args()
        # convert to a dictionary
        self.args_dict = vars(arguments)

        # if we do interface uptime stuff we use this
        self.total_interfaces_info = []
        # this is used if doing a port mapping
        self.port_mapping_info = []

        # if we're counting interface stats  or doing a port mapping lets remove the old files first
        try:
            if self.args_dict['interface_uptime_check']:
                os.remove('input_output_interfaces.xlsx')
            elif self.args_dict['port_mapping']:
                os.remove('port_mapping.xlsx')
        except:
            pass

        # kick off the threading
        self.do_thread()

        # at this point when control has returned here we want to make sure all work in queues is complete
        self.work_queue.join()

        # if we have info in the total_interfaces_info we need to write the data thread safe
        if len(self.total_interfaces_info) > 0:
            for interface_summary in self.total_interfaces_info:
                napalm_common_operations.excel_workbook_creation(interface_summary)

        # if we did a port mapping run this
        if len(self.port_mapping_info) > 0:
            napalm_common_operations.port_mapping_excel_creation(
                ports_summary=self.port_mapping_info,
                output_file=self.args_dict['port_mapping_output_file'],
                image_file=self.args_dict['image_filename']
            )

    def do_thread(self):
        # we need the password to use to connect
        password = getpass('Enter the password to use to connect to hosts:')
        # we'll store all our hosts in a queue eventually
        self.work_queue = Queue(maxsize=0)
        # open file to read in host list
        hosts = pd.read_excel(self.args_dict['file_name'])
        # iterate through and add all hosts to the queue
        for index, value in hosts.iterrows():
            self.work_queue.put(
                {
                    'site_name': value['Site Name'],
                    'host': value['IP Address'],
                    'device_role': value['Device Role'],
                    'device_type': value['Device Type'],
                    'device_hostname': value['Device Hostname'],
                    'closet': value['Closet Name']
                }
            )
        # now we kick off our threads
        for i in range(int(self.args_dict['thread_max'])):
            worker_thread = threading.Thread(
                target=self.do_work,
                name=f'worker_thread_number_{i}',
                kwargs={
                    'password': password
                }
            )
            # daemonize the thread
            worker_thread.setDaemon(True)
            # start the thread
            worker_thread.start()

    def do_work(self, password):
        # while our queue isn't empty
        while not self.work_queue.empty():
            try:
                # lets get our host info
                host_info = self.work_queue.get()
                print(f'beginning work on host {host_info["device_hostname"]} at ip {host_info["host"]}')

                # lets try to connect
                network_connection = napalm_common_operations.connect_to_network_device(
                    host=host_info['host'],
                    username=self.args_dict['username'],
                    password=password,
                    device_type=host_info['device_type']
                )
                # if the connection failed...False was returned and we just skip this
                if network_connection:

                    # now do work depending on what arguments were passed
                    # should we write the full config to a file
                    if self.args_dict['get_config']:
                        napalm_common_operations.get_full_config(network_connection=network_connection,
                                                                 hostname=host_info['device_hostname'])

                    # should we check link health of any interface with ospf neighbors?
                    if self.args_dict['check_ospf_link_health']:
                        pass
                        # napalm_common_operations.check_ospf_link_health(network_connection=network_connection)

                    # should we check interface uptime info
                    if self.args_dict['interface_uptime_check']:
                        results = napalm_common_operations.interface_uptime_check(network_connection=network_connection,
                                                                        device_type=host_info['device_type'])
                        # append the results to the list, we'll go through this later
                        self.total_interfaces_info.append(results)

                    # if doing a port mapping
                    if self.args_dict['port_mapping']:
                        results = napalm_common_operations.port_mapping(network_connection=network_connection)
                        # we want to add the switches to the proper closet info sub-list
                        # if the sub-list doesn't exist though we need to add it
                        try:
                            # we get the index number of the closet name in the outer list so we can append to it
                            closet_index = [
                                i for i, d in enumerate(self.port_mapping_info) if host_info['closet'] in d.keys()
                            ]
                            # now append the info to the sub-list
                            self.port_mapping_info[closet_index[0]][host_info['closet']].append(results)
                        except Exception as e:
                            self.port_mapping_info.append({host_info['closet']: [results]})
                        #self.port_mapping_info.append(results)

                    # should we upgrade legacy tacacs config if it exists?
                    if self.args_dict['tacacs_legacy_upgrade']:
                        pass
                        # # napalm relies on scp server to be enabled for config changes, if not enabled...we need to do so
                        # # use netmiko since config changes in napalm rely on scp server to upload the candidate config
                        # if not napalm_common_operations.check_scp_server(network_connection=network_connection):
                        #     print(f'enabling scp server on host {host_info["host"]}')
                        #     # pass info to netmiko to enable scp server
                        #     napalm_common_operations.enable_scp_server(
                        #         host=host_info['host'],
                        #         username=self.args_dict['username'],
                        #         password=password,
                        #         device_type=host_info['device_type']
                        #     )
                        # napalm_common_operations.convert_tacacs_legacy_to_new_format(
                        #     network_connection=network_connection, host=host_info["host"])

                else:
                    print(f'completing work on host {host_info["device_hostname"]} at ip {host_info["host"]} due to error')


                # disconnect from the network device
                napalm_common_operations.disconnect_from_network_device(network_connection=network_connection)
            except Exception as e:
                print(f'an Exception occurred while connecting\n{e}')
            finally:
                # signal queue entry work is done
                self.work_queue.task_done()

if __name__ == '__main__':
    main = Main()