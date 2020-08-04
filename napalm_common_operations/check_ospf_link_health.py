from napalm import get_network_driver
import textfsm
import json

def check_ospf_link_health(network_connection):
    '''
    find interfaces with ospf neighbor adjacencies and collect statistics on them
    :param network_connection:
    :return:
    '''
    get_ospf_neighbors = 'show ip ospf neighbor | begin Neighbor'
    # our template to use
    template_file = 'textfsm_templates/show_ip_ospf_neighbors.textfsm'
    # get the cmd output
    output = network_connection.cli([get_ospf_neighbors])
    # open the template file
    with open(template_file) as f:
        template = textfsm.TextFSM(f)
        # convert the results
        parsed_output = template.ParseText(output['show ip ospf neighbor | begin Neighbor'])
    # list of interfaces we will check out
    interface_list = [i[len(i) - 1] for i in parsed_output]
    print(interface_list)

    try:
        # get counters for every interface
        full_counters = network_connection.get_interfaces_counters()
        # print counters if interface matches
        for interface in interface_list:
            if interface in full_counters:
                print(f'Counters for interface {interface} are:\n{json.dumps(full_counters[interface], indent=1)}')

    except Exception as e:
        print(f'Error occurred getting interface stats')

    # get optics info
    print(json.dumps(network_connection.get_optics(), indent=1))