"""
DOCSTRING
"""

import requests
import urllib3

# Disable Self-Signed SSL Warning #
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Cloupia REST API Key #
CLOUPIA_KEY = "<PASTE CLOUPIA KEY HERE>"

# UCSD Address #
UCSD_ADDR = "<PASTE UCSD ADDRESS HERE>"

# REST API URL #
API_URL = "<PASTE API URL HERE>"

# XML Payload from UCSD #
API_CALL = """
<PASTE API CALL HERE>
"""

# Execute REST API #
XML_URL = "https://" + UCSD_ADDR + API_URL
XML_HEADER = "<?xml version=\"1.0\" encoding=\"utf-8\"?>"
DATA = XML_HEADER + API_CALL.replace('\n', '')
HEADERS = {'Content-Type': 'application/xml', 'X-Cloupia-Request-Key': CLOUPIA_KEY}
RESPONSE = requests.post(XML_URL, headers=HEADERS, data=DATA, timeout=30, verify=False)

# Print Results
print(RESPONSE)
# print(RESPONSE.content)
