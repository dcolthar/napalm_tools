from napalm import get_network_driver
import textfsm
import textwrap

def convert_tacacs_legacy_to_new_format(network_connection, host):
    # the list of commands to run against the host when all is said and done
    final_conversion_command_list = []

    # command we will use to find if any legacy hosts exist and the aaa group they are in and if scp enabled
    cmd = 'show run | sec tacacs-server'
    group_cmd = 'show run | sec aaa group server tacacs+'

    # get the results
    results = network_connection.cli([cmd, group_cmd])

    # if we have any aaa server groups lets get that info now
    if results['show run | sec aaa group server tacacs+']:
        # lets see if the old host was in a AAA group
        aaa_group_template_file = 'textfsm_templates/show_run_section_aaa_group_server_tacacs.textfsm'
        # open the template file
        with open(aaa_group_template_file) as f2:
            # set our template
            aaa_template = textfsm.TextFSM(f2)
            # parse the output
            aaa_group_parsed_results = aaa_template.ParseText(results['show run | sec aaa group server tacacs+'])
            ## print(aaa_group_parsed_results)

    # if there was any output at all from the legacy server gathering...
    if results['show run | sec tacacs-server']:
        print(f'legacy tacacs config found on host {host}!')
        # get the output of the command
        value = results['show run | sec tacacs-server']

        # the textfsm template to conversion of legacy host commands
        legacy_tacacs_template_file = 'textfsm_templates/show_tacacs_include_tacacs-server.textfsm'
        # now open the template file
        with open(legacy_tacacs_template_file) as f:
            # set our template
            template = textfsm.TextFSM(f)
            # parse the output
            parsed_results = template.ParseText(value)

            # go through each entry
            for entry in parsed_results:
                # now time to convert to a new command format
                old_format_removal = f'no tacacs-server host {entry[0]} key {entry[1]}'
                new_format_add = textwrap.dedent(f'''
                    tacacs server TACACS_SERVER_{entry[0]}
                    address ipv4 {entry[0]}
                    key {entry[1]}
                ''')

                # now we have to see if this host was part of any aaa server-groups
                for group in aaa_group_parsed_results:
                    if entry[0] in group:
                        ### print(f'host {entry[0]} is in aaa group {group[0]}')
                        # lets add the command to remove this guy from the group
                        # also add the new host even though it is not defined yet
                        final_conversion_command_list.append(textwrap.dedent(
                            f'''
                                aaa group server tacacs+ {group[0]}
                                no server {entry[0]}
                                server name TACACS_SERVER_{entry[0]}
                            '''
                        ))
                # now that all servers are removed from the groups..we can remove the old servers and add new
                final_conversion_command_list.append(old_format_removal)
                final_conversion_command_list.append(new_format_add)

            # now that we've looped through...final config command time
            # merge_candidate_config requires a file to read from
            candidate_config_file = 'config_output/temp_file.txt'
            with open(candidate_config_file, 'w') as output_file:
                for cmd_entry in final_conversion_command_list:
                    output_file.write(cmd_entry)

            # we're going to write to the candidate config now
            ### print(f'loading the candidate config for host {host}')
            network_connection.load_merge_candidate(candidate_config_file)
            # print the difference in the candidate and the running config
            ### print(network_connection.compare_config())

            # commit the changse
            print(f'commiting candidate config for {host}')
            #network_connection.commit_config()
            network_connection.discard_config()


    else:
        # results must have been empty
        print(f'no legacy tacacs host config format found on host {host}')
