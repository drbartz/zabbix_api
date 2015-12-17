try:
    import simplejson as json
except ImportError:
    import json

import urllib2, socket
import cPickle as pickle
from time import strftime, localtime

def postRequest(obj):
    #print obj
    request = urllib2.Request("http://127.0.0.1/zabbix/api_jsonrpc.php")
    request.add_header('Content-Type' , 'application/json-rpc')
    request.add_header('User-agent', 'script_by_Mateus/1.0')
    response = urllib2.urlopen(request, json.dumps(obj))
    #print 'Receive: %s' % content
    return json.loads(response.read())

class api:
    def __init__(self):
        self.obj={'jsonrpc': '2.0', 'params':{}}
        self.api_translate={}
        self.history={}
        # translate from: https://www.zabbix.com/documentation/2.4/manual/api/reference/action/object
        self.api_translate["action"] = {
                "eventsource": "check event->source",
                "filter": {
                    "conditions": {
                        "conditiontype": {
                            # Possible values for trigger actions: 
                            "host group": 0,
                            "host": 1,
                            "trigger": 2,
                            "trigger name": 3,
                            "trigger severity": 4,
                            "trigger value": 5,
                            "time period": 6,
                            "host template": 13,
                            "application": 15,
                            "maintenance status": 16,
    
                            # Possible values for discovery actions:
                            "host IP": 7,
                            "discovered service type": 8,
                            "discovered service port": 9,
                            "discovery status": 10,
                            "uptime or downtime duration": 11,
                            "received value": 12,
                            "discovery rule": 18,
                            "discovery check": 19,
                            "proxy": 20,
                            "discovery object": 21,
    
                            # Possible values for auto-registration actions: 
                            "proxy": 20,
                            "host name": 22,
                            "host metadata": 24,
    
                            # Possible values for internal actions: 
                            "host group": 0,
                            "host": 1,
                            "host template": 13,
                            "application": 15,
                            "event type": 23,
                        },
                        "operator":{
                            "(default) =": 0,
                            "<>": 1,
                            "like": 2,
                            "not like": 3,
                            "in": 4,
                            ">=": 5,
                            "<=": 6,
                            "not it": 7,
                        }
                    },
                    "evaltype": {
                        "and/or" : 0, 
                        "and" : 1, 
                        "or": 2, 
                        "custom expression":3 
                    }
                },
                    
                "status": {
                    "(default) enabled":0,
                    "disabled":1
                }
        }
        
        # translate from: https://www.zabbix.com/documentation/2.4/manual/api/reference/event/object
        self.api_translate["event"] = {
                "source": { 
                    "event created by a trigger":    0,
                    "event created by a discovery rule": 1,
                    "event created by active agent auto-registration": 2, 
                    "internal event": 3 
                }
        }

        # translate from: https://www.zabbix.com/documentation/2.4/manual/api/reference/trigger/object
        self.api_translate["trigger"] = {
                "priority": { 
                    "(default) not classified":    0,
                    "information":    1,
                    "warning":    2,
                    "average":    3,
                    "high":    4,
                    "disater":    5,
                }
        }

    ''' 
    Authenticate and use the token on the next request 
    '''
    def login(self, user, password):
        self.obj["params"]["user"]=user
        self.obj["params"]["password"]=password
        self.obj["method"]="user.login"
        self.obj["id"]=1
        self.obj["auth"]=postRequest(self.obj)["result"]
        #print self.obj

    ''' 
    Check if a action name exist
        return True/False
    '''
    def Exist_action_by_Name(self, name):
        exists = False
        self.obj["result"]={}
        self.generic_method("action.exists", { "name": name})
        if "result" in self.obj:
                exists=self.obj["result"]
        return exists 

    '''
    self explain
    '''
    def Create_Hostgroup(self, hostgroup_name):
        if self.Hostgroup_Exist_by_Name(hostgroup_name):
            print "OK: hostgroup[%s] already exist" % (hostgroup_name)
        else:
            self.obj["result"]={}
            self.generic_method("hostgroup.create", { "name": hostgroup_name})
            if "groupids" in self.obj["result"]:
                print "OK: hostgroup[%s] created" % hostgroup_name
            else:
                print "ERR: can't create hostgroup[%s]" % hostgroup_name

    ''' 
    return a list of hostgroup id that a hostname is a member
    '''
    def Host_Get_HostGroupIdList_by_HostName(self,hostname):
        list = []
        self.obj["result"]={}
        self.generic_method("host.get", { "output": ["hostid"], "selectGroups": ["groupid"],"filter": { "host": hostname } })
        if "groups" in self.obj["result"][0]:
            for groups in self.obj["result"][0]["groups"]:
                if "groupid" in groups:
                    list.append(int(groups["groupid"]))
        return list
    
    ''' 
    Add a hostname to a hostgroup
    '''
    def Host_Update_Add_HostGroup_by_Name(self,hostname,hostgroup_name):
        if self.Hostgroup_Exist_by_Name(hostgroup_name):
            if self.Hostname_Exists(hostname):
                Current=self.Host_Get_HostGroupIdList_by_HostName(hostname)
                groupid=self.Hostgroup_Get_Hostgroupid_by_Name(hostgroup_name)
                if groupid in Current:
                    print "OK: Hostname[%s] already in HostGroup[%s]" % (hostname,hostgroup_name)
                else:
                    Current.append(int(groupid))
                    hostid=self.Host_Get_HostId_by_Hostname(hostname)
                    print "OK: Adding Hostname[%s] to Hostgroup[%s]" % (hostname,hostgroup_name)
                    PARAM={"hostid":hostid,"groups": [] }
                    for ID in Current:
                        PARAM["groups"].append({ "groupid": ID })
                    self.generic_method("host.update", PARAM)
            else:
                print "ERR: hostname[%s] not found" % (hostname)
        else:
            print "ERR: hostgroup[%s] not found" % (hostgroup_name)

    ''' 
    return the hostgroup_id to a hostgroup_name
    '''
    def Hostgroup_Get_Hostgroupid_by_Name(self,hostgroup_name):
        id=0    
        self.obj["result"]={}
        self.generic_method("hostgroup.get", { "output": "extended", "filter": { "name": [hostgroup_name]} } )
        if "result" in self.obj:
            for response in self.obj["result"]:
                if "groupid" in response:
                    id=int(response["groupid"])
        return id
    
    ''' 
    return the if the hostgroup_name exist (true/false)
    '''
    def Hostgroup_Exist_by_Name(self,hostgroup_name):
        test=False    
        self.obj["result"]={}
        self.generic_method("hostgroup.exists", {  "name": hostgroup_name } )
        if "result" in self.obj:
            test=int(self.obj["result"])
        return test

    ''' 
    return the if the template_name exist (true/false)
    '''
    def Template_Exist(self,hostgroup_name):
        test=False    
        self.obj["result"]={}
        self.generic_method("template.exists", {  "name": hostgroup_name } )
        if "result" in self.obj:
            test=int(self.obj["result"])
        return test


    ''' 
    return the template_id to a template_name
    '''
    def Template_Get_Templateid_by_Name(self, name):
        templateid = 0
        self.obj["result"]={}
        self.generic_method("template.get", { "output": ["hostid"], "filter": { "host": name } })
        if "templateid" in self.obj["result"][0]:
                templateid=self.obj["result"][0]["templateid"]
        return templateid 

    ''' 
    return the if the hostname exist (true/false)
    '''
    def Hostname_Exists(self, hostname):
        test = False
        self.obj["result"]={}
        self.generic_method("host.exists", { "host": hostname } )
        if "result" in self.obj:
                test=self.obj["result"]
        return test

    ''' 
    return a list of template_id for a hostname 
    '''
    def Host_Get_TemplateIdList_by_Hostname(self, hostname):
        list = []
        self.obj["result"]={}
        self.generic_method("host.get", { "output": ["hostid"], "selectParentTemplates": ["templateid"],"filter": { "host": hostname } })
        if "parentTemplates" in self.obj["result"][0]:
            for template in self.obj["result"][0]["parentTemplates"]:
                list.append(int(template["templateid"]))
        return list

    ''' 
    return the host_id to a hostname
    '''
    def Host_Get_HostId_by_Hostname(self, hostname):
        id = 0
        self.obj["result"]={}
        output=self.generic_method("host.get", { "output": ["hostid"], "filter": { "host": hostname } })
        if "hostid" in self.obj["result"][0]:
                id = self.obj["result"][0]["hostid"]
        return id

    ''' 
    create a autoregister action for a S.O and add a template_name
    '''
    def Action_Create_Autoregister_by_Name(self, autoregister_name, SO_name, template_name):
        templateid = 0
        if self.Exist_action_by_Name(autoregister_name):
            print "OK: Auto Registration[%s] Action already exist" % (autoregister_name)
        else:
            templateid = self.Template_Get_Templateid_by_Name(template_name)
            self.obj["result"]={}
            PARAM={
               "name": autoregister_name,
               "eventsource": zabbix_api.api_translate["event"]["source"]["event created by active agent auto-registration"],
               "status": zabbix_api.api_translate["action"]["status"]["(default) enabled"],
               "esc_period": 0,
               "filter": {
                  "evaltype": zabbix_api.api_translate["action"]["filter"]["evaltype"]["and/or"],
                  "conditions": [ {
                     "conditiontype": zabbix_api.api_translate["action"]["filter"]["conditions"]["conditiontype"]["host metadata"],
                     "operator": zabbix_api.api_translate["action"]["filter"]["conditions"]["operator"]["like"],
                     "value": SO_name
                  } ]
               },
                   "operations": [
                  {
                     "esc_step_from": 1,
                     "esc_period": 0,
                     "optemplate": [
                        { "templateid": templateid }
                     ],
                     "operationtype": 6,
                     "esc_step_to": 1
                  }
               ]
            }
            self.generic_method("action.create", PARAM)
            if "actionids" in self.obj["result"]:
                print "OK: Add Auto Registration[%s] Action with ID[%s]" % (autoregister_name, str(self.obj["result"]["actionids"]))

    ''' 
    Add a template to a hostname
    '''
    def Host_Update_Add_Template_by_Name(self, hostname, templatename):
        if self.Template_Exist(templatename):
            templateid = self.Template_Get_Templateid_by_Name(templatename)
            if self.Hostname_Exists(hostname):
                hostid = self.Host_Get_HostId_by_Hostname(hostname)
                Template_List=self.Host_Get_TemplateIdList_by_Hostname(hostname)
                if int(templateid) in Template_List: 
                    print "OK: Hostname[%s] already has the template [%s]" % (hostname,templatename)
                else:
                    Template_List.append(int(templateid))
                    print "OK: Adding template[%s] to Hostname[%s]" % (templatename,hostname)
                    PARAM={"hostid":hostid,"templates": [] }
                    for ID in Template_List:
                        PARAM["templates"].append({ "templateid": ID })
                    self.generic_method("host.update", PARAM)
            else:
                print "ERR: Hostname[%s] not found" % (hostname)
        else:
            print "ERR: Template[%s] not found" % (templatename)
                

    ''' 
    Get zabbix status
    '''
    def get_zabbix_statu(self):
        Priority={}
        for item in self.api_translate["trigger"]["priority"]:
            Priority[self.api_translate["trigger"]["priority"][item]]=item

        # read all templates info
        self.generic_method("template.get",{ "output": "extend"})
        for result in zabbix_api.obj["result"]:
            TemplateId=result["templateid"]
            TemplateHost=result["host"]
            if not "template" in self.history: self.history["template"]={}
            if not TemplateId in self.history["template"]: self.history["template"][TemplateId]={"host":TemplateHost}
            #print "templateid[%s] - name[%s]" % ( TemplateId, TemplateHost )

        #
        # Read all hosts information
        self.generic_method("host.get", {"output": "extend"})
        #self.status["host"]={}
        #{u'available': u'1', u'maintenance_type': u'0', u'ipmi_errors_from': u'0', u'ipmi_username': u'', u'snmp_disable_until': u'0', u'ipmi_authtype': u'0', u'ipmi_disable_until': u'0', u'lastaccess': u'0', u'snmp_error': u'', u'ipmi_privilege': u'2', u'jmx_error': u'', u'jmx_available': u'0', u'maintenanceid': u'0', u'snmp_available': u'0', u'status': u'0', u'description': u'', u'host': u'zabbix-server', u'disable_until': u'0', u'ipmi_password': u'', u'templateid': u'0', u'ipmi_available': u'0', u'maintenance_status': u'0', u'snmp_errors_from': u'0', u'ipmi_error': u'', u'proxy_hostid': u'0', u'hostid': u'10105', u'name': u'zabbix-server', u'jmx_errors_from': u'0', u'jmx_disable_until': u'0', u'flags': u'0', u'error': u'', u'maintenance_from': u'0', u'errors_from': u'0'}
        for response in zabbix_api.obj["result"]:
            HostId=response["hostid"]
            Host=response["host"]
            HostName=response["name"]
            if not "host" in self.history: self.history["host"]={}
            if not HostId in self.history["host"]: self.history["host"][HostId]={"host":Host, "name":HostName}

        # read all triggers
        #{u'status': u'0', u'description': u'Zabbix agent on {HOST.NAME} is unreachable for 5 minutes', u'state': u'0', u'url': u'', u'type': u'0', u'templateid': u'10047', u'lastchange': u'1450299270', u'value': u'1', u'priority': u'3', u'triggerid': u'13491', u'flags': u'0', u'comments': u'', u'error': u'', u'expression': u'{12900}=1'}
        self.generic_method("trigger.get",{ "output": ["triggerid", "templateid", "lastchange", "description", "value", "priority"], "selectGroups":"groupid", "selectHosts":"hostid"})
        for response in zabbix_api.obj["result"]:
            TriggerId=response["triggerid"]
            TemplateId=response["templateid"]
            LastChange=response["lastchange"]
            Description=response["description"]
            Value=response["value"]
            Priority=response["priority"]
            if not "trigger" in self.history: self.history["trigger"]={}
            if not TriggerId in self.history["trigger"]: self.history["trigger"][TriggerId]={"templateid":TemplateId, "lastchange":LastChange, "value":Value, "priority":Priority, "description": Description}
            for Hosts in response["hosts"]:
                HostId=Hosts["hostid"]
                if HostId in self.history["host"]: 
                    HostName=self.history["host"][HostId]["name"]
                else:
                    HostName="N/A"
                self.history["trigger"][TriggerId]={"templateid":TemplateId, "lastchange":LastChange, "value":Value, "priority":Priority, "description": Description, "hostname":HostName}
                if int(Value)==1: print "Active trigger [%s] on host [%s] with priority [%s]. Last change [%s]" % (Description, HostName, Priority, LastChange)
    
        # read all events info
        self.generic_method("event.get",{ "output": "extend", "selectHosts":"extend", "sortfield": ["eventid"] })
        for response in zabbix_api.obj["result"]:
            #print response
            # ObjectId = TriggerId
            EventId=response["eventid"]
            EventTime=response["clock"]
            TriggerId=response["objectid"]
            #self.generic_method("trigger.get",{ "output": "extend", "triggerids": response["objectid"] })
            TemplateId=self.history["trigger"][TriggerId]["templateid"]
            if TemplateId in self.history["template"]:
                TemplateHost=self.history["template"][TemplateId]["host"]
            else:
                TemplateHost="N/A"
            TriggerValue=self.history["trigger"][TriggerId]["value"]
            TriggerPriority=self.history["trigger"][TriggerId]["priority"]
            TriggerLastChange=self.history["trigger"][TriggerId]["lastchange"]
            TriggerDescription=self.history["trigger"][TriggerId]["description"]
            if "lastdata" not in self.history: self.history["lastdata"]={}
            if "event" not in self.history["lastdata"]: self.history["lastdata"]["event"]=0
            if EventId>self.history["lastdata"]["event"]:
                Time=strftime("%d/%m/%y %H:%M:%S",localtime(int(response["clock"])))
                LastTime=strftime("%d/%m/%y %H:%M:%S",localtime(int(TriggerLastChange)))
                print "%s - eventid[%s] - templateid[%s] - Host[%s] - TriggerId[%s] - TriggerValue[%s] - TriggerPriority[%s] - TriggerLastChange[%s] - TriggerDescription[%s]"  % (Time, EventId, TemplateId, TemplateHost, TriggerId, TriggerValue, TriggerPriority, LastTime, TriggerDescription)
                self.history["lastdata"]["event"]=EventId
            else:
                print EventId
        
    '''
    Load history
    '''
    def history_load(self, FILE_NAME):
        try:
            with open(FILE_NAME, 'rb') as fp:
                data = pickle.load(fp)
        except:
            data={}
        self.history=data

    '''
    Save history
    '''
    def history_save(self, FILE_NAME):
        with open(FILE_NAME, 'wb') as fp:
            pickle.dump(self.history, fp)

    ''' 
    Generic request method
    '''
    def generic_method(self, method, params):
        self.obj["method"] = method
        self.obj["params"] = params
        #self.obj["id"] = self.obj["id"] +1
        output=postRequest(self.obj)
        if "result" in output:
            self.obj["result"]=output["result"]
        else:
            print "Error, can't retrive data for---------------:", self.obj
            print "--------------------------------------------:"

#####print zabbix_api.api_translate
hostname = socket.gethostname()

print socket.gethostname().split(".")[0]
zabbix_api = api()
zabbix_api.login("admin", "zabbix")
zabbix_api.history_load(".api_history")
#zabbix_api.Action_Create_Autoregister_by_Name("Linux autoregistration", "Linux", "Template OS Linux")
#zabbix_api.Action_Create_Autoregister_by_Name("Windows autoregistration", "Windows", "Template OS Windows")
#zabbix_api.Host_Update_Add_Template_by_Name(hostname, "Template App Zabbix Server")
#zabbix_api.Host_Update_Add_Template_by_Name(hostname, "Template OS Linux")
#zabbix_api.Create_Hostgroup("Monitoring")
#zabbix_api.Host_Update_Add_HostGroup_by_Name(hostname,"Monitoring")
zabbix_api.get_zabbix_statu()
zabbix_api.history_save(".api_history")
