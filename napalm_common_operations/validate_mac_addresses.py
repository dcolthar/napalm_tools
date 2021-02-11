import textfsm
import pandas as pd
import json

def valiate_mac_table(mac_input_file, network_connection):
    # the textfsm template to use
    mac_template_file = 'textfsm_templates/show_mac_address.textfsm'
    arp_template_file = 'textfsm_templates/show_ip_arp.textfsm'
    # mac table dumps go to this subfolder at first unless they've been moved
    mac_table_folder = 'mac_tables'
    # get device hostname
    hostname = network_connection.get_facts()['hostname']
    # open the mac_address_file
    print(f'Reading MAC addresses in from host {hostname}')
    mac_input = pd.read_excel(f'{mac_table_folder}/{mac_input_file}', sheet_name=hostname, keep_default_na=False)
    # time to get the mac address table, we can check this against the old values after
    # the cmd to run with napalm
    cmd1 = 'show mac address-table dynamic'
    cmd2 = 'show ip arp'
    results = network_connection.cli([cmd1, cmd2])
    # time to parse the results, first need to open and set the template for the mac table
    total_mac_table = []
    with open(mac_template_file) as f:
        template = textfsm.TextFSM(f)
        mac_parsed_results = template.ParseText(results[cmd1])
    with open(arp_template_file) as f:
        template = textfsm.TextFSM(f)
        arp_parsed_results = template.ParseText(results[cmd2])
        #print(arp_parsed_results)
    # now to merge the two tables
    for i in mac_parsed_results:
        for j in arp_parsed_results:
            if 'vlan' in j[5].lower() and 'incomplete' not in j[3].lower():
                if i[0] == j[3]:
                    # see if we already have this mac, sometimes we get duplicates and two arps when a phone
                    # first pulls an ip
                    input_data = {'mac': i[0], 'vlan': str(j[5][4::]), 'interface': i[3], 'arp_age': j[2]}
                    total_mac_table.append(input_data)

    # print(json.dumps(total_mac_table))
    # print(len(total_mac_table))

    # this dictionary will hold any interfaces that do NOT match with old values
    problem_macs = []
    found_macs = []
    # now go into each MAC address entry and check
    for index, value in mac_input.iterrows():
        # only check the MAC if there is an IP address in the field
        # this will help eliminate phones that jump on data vlan and then move to voice
        if value['IP Address']:
            old_mac = value['MAC Address Learned']
            old_vlan = str(value['VLAN'])
            old_interface = value['Interface']
            # go through the mac table dump
            for mac_entry in total_mac_table:
                if old_mac == mac_entry['mac']:
                    #print(f'mac {mac_entry["mac"]} was found in the mac dump!')
                    found_macs.append(mac_entry['mac'])
                    if old_vlan != mac_entry['vlan']:
                        problem_macs.append(
                            {
                                'old_interface': old_interface,
                                'new_interface': mac_entry['interface'],
                                'mac_address': mac_entry['mac'],
                                'old_vlan': old_vlan,
                                'new_vlan': mac_entry['vlan'],
                                'hostname': hostname
                            }
                        )
    # now go through and see if any macs are NOT found
    for index, value in mac_input.iterrows():
        if value['IP Address']:
            if value['MAC Address Learned'] not in found_macs:
                problem_macs.append(
                    {
                        'old_interface': value['Interface'],
                        'new_interface': 'NOT_FOUND',
                        'mac_address': value['MAC Address Learned'],
                        'old_vlan': value['VLAN'],
                        'new_vlan': 'NOT_FOUND',
                        'hostname': hostname
                    }
                )

    # if we have any entries in problem macs...
    if problem_macs:
        print(f'Host {hostname} has some MAC Addresses with issues!')
        # for i in problem_macs:
        #     print(json.dumps(i, indent=1))
        pd.set_option('display.max_rows', None)
        df = pd.DataFrame(problem_macs)
        print(df)


