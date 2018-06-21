"""
DOCSTRING
"""

import os
import sys
import json
import socket
import platform
import requests
import urllib3
from pathlib import Path

# Disable Self-Signed SSL Warning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

UCSD_ADDR = ""
CLOUPIA_KEY = ""

# JSON Object Class #
class JsonObj(dict):
    """
    DOCSTRING
    """

    def __init__(self, *args, **kwargs):
        super(JsonObj, self).__init__(*args, **kwargs)
        for arg in args:
            if isinstance(arg, dict):
                for key, value in arg.items():
                    if isinstance(value, dict):
                        self[key] = JsonObj(value)
                    else:
                        self[key] = value

        if kwargs:
            for key, value in kwargs.items():
                self[key] = value

    def __getattr__(self, attr):
        return self.get(attr)

    def __setattr__(self, key, value):
        self.__setitem__(key, value)

    def __setitem__(self, key, value):
        super(JsonObj, self).__setitem__(key, value)
        self.__dict__.update({key: value})

    def __delattr__(self, item):
        self.__delitem__(item)

    def __delitem__(self, key):
        super(JsonObj, self).__delitem__(key)
        del self.__dict__[key]

# UCSD Object Class #
class UcsdModule(JsonObj):
    """
    DOCSTRING
    """

    def __init__(self, *args, **kwargs):
        super(UcsdModule, self).__init__(*args, **kwargs)
        for arg in args:
            if isinstance(arg, dict):
                for key, value in arg.items():
                    if isinstance(value, dict):
                        self[key] = UcsdModule(value)
                    else:
                        self[key] = value

        if kwargs:
            for key, value in kwargs.items():
                self[key] = value

    def get_module_name(self):
        """
        DOCSTRING
        """

        return self.moduleName

    def get_operation_type(self):
        """
        DOCSTRING
        """

        return self.operationType

    def get_api(self):
        """
        DOCSTRING
        """

        return self.apiCall

    def get_api_type(self):
        """
        DOCSTRING
        """

        return self.apiType

    def to_json(self):
        """
        DOCSTRING
        """

        return json.dumps(self.modulePayload, indent=4)

    def to_xml(self):
        """
        DOCSTRING
        """

        xml_temp = ""
        xml_temp += "<cuicOperationRequest>"

        if self.operationType:
            xml_temp += "<operationType>"
            xml_temp += self.operationType
            xml_temp += "</operationType>"

        xml_temp += "<payload>"
        xml_temp += "<![CDATA["
        xml_temp += ("<" + self.get_module_name() + ">")

        xml_temp += self.generate_xml(self.modulePayload.param0)

        xml_temp += ("</" + self.get_module_name() + ">")
        xml_temp += "]]>"
        xml_temp += "</payload>"
        xml_temp += "</cuicOperationRequest>"

        return xml_temp

    def generate_xml(self, xml_obj):
        """
        DOCSTRING
        """
        xml_text = ""

        for xml_prop in xml_obj:
            if isinstance(xml_obj[xml_prop], UcsdModule):
                xml_text += ("<" + str(xml_prop) + ">")
                xml_text += self.generate_xml(xml_obj[xml_prop])
                xml_text += ("</" + str(xml_prop) + ">")
            elif isinstance(xml_obj[xml_prop], list):
                for i in range(len(xml_obj[xml_prop])):
                    xml_text += ("<" + str(xml_prop) + ">")
                    xml_text += self.generate_xml(xml_obj[xml_prop][i])
                    xml_text += ("</" + str(xml_prop) + ">")
            else:
                xml_text += ("<" + str(xml_prop) +
                             ">" + str(xml_obj[xml_prop]) +
                             "</" + str(xml_prop) + ">")

        return xml_text

# Set UCSD Address #
def set_ucsd_addr(addr):
    """
    DOCSTRING
    """

    global UCSD_ADDR

    UCSD_ADDR = addr

# Get UCSD Address #
def get_ucsd_addr():
    """
    DOCSTRING
    """

    return UCSD_ADDR

# Set Cloupia Key #
def set_cloupia_key(key):
    """
    DOCSTRING
    """

    global CLOUPIA_KEY

    CLOUPIA_KEY = key

# Get Cloupia Key #
def get_cloupia_key():
    """
    DOCSTRING
    """

    return CLOUPIA_KEY

# Validate IP Address #
def valid_ip(ip_addr):
    """
    DOCSTRING
    """

    try:
        socket.inet_aton(ip_addr)
        return True
    except socket.error:
        return False
    else:
        return False

# Get Operating System #
def get_os():
    return platform.system()

# Get Module Path #
def get_resource_path(resource):
    """
    DOCSTRING
    """

    resource_path = ""
    curr_path = Path().resolve().parent

    if get_os() == "Windows":
        resource_path = "\\" + resource + "\\"
    elif get_os() == "Linux" or get_os == "Darwin":
        resource_path = "/" + resource + "/"

    res_path = str(curr_path) + resource_path

    return res_path

# Import Modules in Module Folder #
def create_ucsd_module(mod_key):
    """
    DOCSTRING
    """

    key_path = mod_key + ".json"

    json_obj = open(get_resource_path("modules") + key_path, "r")
    mod_obj = json.loads(json_obj.read())

    new_module = UcsdModule(mod_obj)

    return new_module

def list_modules():
    """
    DOCSTRING
    """

    modules = []
    files = os.listdir(get_resource_path("modules"))

    for file in enumerate(files):
        name_split = file[1].split(".")
        modules.append(name_split[0])

    return modules

# UCSD API Request Call #
def call_ucsd_api(module):
    """
    DOCSTRING
    """
    api_timeout = 120

    if module.get_api_type() == "xml":
        xml_url = "https://" + get_ucsd_addr() + module.get_api()
        headers = {'Content-Type': 'application/xml', 'X-Cloupia-Request-Key': CLOUPIA_KEY}
        xml_header = "<?xml version=\"1.0\" encoding=\"utf-8\"?>"
        data = xml_header + module.to_xml()

        if module.get_operation_type() == "UPDATE":
            response = requests.put(xml_url, headers=headers, data=data, timeout=api_timeout, verify=False)
        else:
            response = requests.post(xml_url, headers=headers, data=data, timeout=api_timeout, verify=False)

    elif module.get_api_type() == "json":
        json_url = "https://" + get_ucsd_addr() + module.get_api() + str(module.to_json())
        headers = {'Content-Type': 'application/json', 'X-Cloupia-Request-Key': CLOUPIA_KEY}

        response = requests.post(json_url, headers=headers, timeout=api_timeout, verify=False)

    else:
        print("ERROR!!!")

    return response
