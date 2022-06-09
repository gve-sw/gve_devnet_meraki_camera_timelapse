#!/usr/bin/python

""" Copyright (c) 2020 Cisco and/or its affiliates.
This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at
           https://developer.cisco.com/docs/licenses
All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied. 
"""

from flask import Flask, render_template, request
from dotenv import load_dotenv
from meraki import DashboardAPI
import json, os, requests
app = Flask(__name__)


@app.route('/', methods=["GET", "POST"])
def index():
    
    selected_org=None
    selected_network=None
    selected_cam=None
    
    if request.method == "POST":
        selected_org=request.form.get('organizations_select')
        selected_network=request.form.get('network')
        selected_cam=request.form.get('cam_select')
        
        # Go To Step 2
        if selected_cam == None:
            return render_template('home.html', hiddenLinks=True, dropdown_content=get_orgs_and_networks(), selected_elements={'organization':selected_org, 'networkid':selected_network},  dropdown_content1=get_cameras(selected_org, selected_network))
        # Go To Step 3
        else:
            try:
                img=get_snapshot(selected_cam)
                return render_template('home.html', hiddenLinks=True, dropdown_content=get_orgs_and_networks(), selected_elements={'organization':selected_org, 'networkid':selected_network},success=True, snapshot=img)
            except:
                return render_template('home.html', hiddenLinks=True, dropdown_content=get_orgs_and_networks(), selected_elements={'organization':selected_org, 'networkid':selected_network}, error=True)

        
    
    return render_template('home.html', dropdown_content=get_orgs_and_networks(), selected_elements={'organization':selected_org, 'networkid':selected_network})



def get_orgs_and_networks():
    apikey = os.environ['API-Key']
    m = DashboardAPI(apikey)
    result = []
    for org in m.organizations.getOrganizations():
        org_entry = {
            "orgaid" : org['id'],
            "organame" : org['name'],
            "networks" : []
        }
        for network in m.organizations.getOrganizationNetworks(org['id']):
            org_entry['networks'] += [{
                'networkid' : network['id'],
                'networkname' : network['name']
            }]
        result += [org_entry]
    return result

def get_cameras(selected_org,selected_network):
    apikey = os.environ['API-Key']
    url = "https://api.meraki.com/api/v1/organizations/"+ selected_org+ "/devices?networkIds[]="+selected_network+"&productTypes[]=camera"

    payload = None

    headers = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "X-Cisco-Meraki-API-Key": apikey
}

    response = requests.get(url, headers=headers, data = payload).json()
    result=[]
    for cam in response:
        cam_entry={
            "camid" : cam['serial'],
            "camname" : cam['name'],
            
        }
        result += [cam_entry]
    
    return result

def get_snapshot(selected_cam):
    apikey = os.environ['API-Key']
    url = "https://api.meraki.com/api/v1/devices/" + selected_cam + "/camera/generateSnapshot"

    payload = '''{
    
    "fullframe": false

    }'''

    headers = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "X-Cisco-Meraki-API-Key": apikey
    }

    response = requests.request('POST', url, headers=headers, data = payload)
    response= response.text
    img = json.loads(response)
    return img['url']
    
    

if __name__ == '__main__':
    load_dotenv()
    app.run(port=5004,debug=True)
    