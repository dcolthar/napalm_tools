# napalm_tools
Collection of tools using napalm, most if not all read from a host file to pull in info for hosts to connect to.  An example host file is in host_file.xlsx.  As of now works with IOS/IOS-XE for all items working on NXOS and EOS.

Most tools are stored in the folder napalm_common_operations.  Utilizes some textFSM files stored in 'textfsm_tempaltes' folder.

TODO: Add yaml template files for things like column headers to make more dynamic on creation of sheets for port mapping.

## Options
**--file_name** - the name of the host file to read from, defaults to host_file.xlsx
**--get_config** - pull full configuration from devices in the host sheet and store in the config_output folder
**--check_ospf_link_health** - IN PROGRESS
**--tacacs_legacy_upgrade** - IN PROGRESS - need to add verify check to make sure you want to commit changes, for now code is commented out
**--interface_uptime_check** - will make a file named 'input_output_interfaces.xlsx' which has a sheet for each switch.  It will show interfaces that have never had input/ouput,     have frequent input/output and have not had input/output for a long duration of time. NOTE: a lot of cisco gear I ran into showed 'never' for output even on heavily used           interfaces.
**--port_mapping** - will connect to every host and build a closet assessment sheet for each closet as well as the beginning of a port mapping sheet leaving only the physical        patch cable locations to be needed.  NOTE: IN PROGRESS to add auto sizing of the corporate image and the subnets of the routed links
**--port_mapping_output_file** - name of the file to output, default is port_mapping_output.xlsx
**--image_filename** - the image to insert into the closet assessment/port mapping doc, defaults to images/generic_company_logo.jpg
**--thread_max** - max number of threads to run, deafult is 5
**--username** - the username to use to connect to devices, defaults to admin. NOTE: password will be prompted with getpass
