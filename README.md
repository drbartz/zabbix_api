zabbix_api
==========

python script to interact with the Zabbix API

some examples:

	zabbix_api = api()
	zabbix_api.login("My_API_User", "My_Pass")
	zabbix_api.Action_Create_Autoregister_by_Name("Linux autoregistration", "Linux", "Template OS Linux")
	zabbix_api.Action_Create_Autoregister_by_Name("Windows autoregistration", "Windows", "Template OS Windows")
	zabbix_api.Host_Update_Add_Template_by_Name(hostname, "Template App Zabbix Server")
	zabbix_api.Host_Update_Add_Template_by_Name(hostname, "Template OS Linux")
	zabbix_api.Create_Hostgroup("Monitoring")
	zabbix_api.Host_Update_Add_HostGroup_by_Name(hostname,"Monitoring")
