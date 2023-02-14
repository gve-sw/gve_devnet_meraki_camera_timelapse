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
from flask import send_file as flask_send_file
from dotenv import load_dotenv
from meraki import DashboardAPI
import datetime, time
import json, os, requests, imageio
app = Flask(__name__)

# Index
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
                start_date = request.form.get('start_date')
                start_time = request.form.get('start_time')
                end_date = request.form.get('end_date')
                end_time = request.form.get('end_time')
                interval = request.form.get('s')

                nb_snapshots = get_snapshots(selected_cam, start_date, start_time, end_date, end_time, interval)
                make_gif(nb_snapshots)

                return render_template('home.html', hiddenLinks=True, dropdown_content=get_orgs_and_networks(), selected_elements={'organization':selected_org, 'networkid':selected_network},success=True)
            except Exception as e:
                print(e)
                return render_template('home.html', hiddenLinks=True, dropdown_content=get_orgs_and_networks(), selected_elements={'organization':selected_org, 'networkid':selected_network}, error=True)

        
    
    return render_template('home.html', dropdown_content=get_orgs_and_networks(), selected_elements={'organization':selected_org, 'networkid':selected_network})

# Download the timelapse GIF
@app.route('/download', methods=["GET", "POST"])
def download_timelapse():
    return flask_send_file("./snapshots/timelapse.gif", mimetype="image/gif")

# Returns a list of organisations and networks for the given API key
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

# List the cameras available in the selected network
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

# Downloads camera snapshots and stores them in a 'snapshots' folder
def get_snapshots(selected_cam, start_date, start_time, end_date, end_time, interval):
    apikey = os.environ['API-Key']
    snapshot_url = "https://api.meraki.com/api/v1/devices/" + selected_cam + "/camera/generateSnapshot"

    start = datetime.datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M")
    end = datetime.datetime.strptime(f"{end_date} {end_time}", "%Y-%m-%d %H:%M")

    current_time = start
    i=0

    while current_time < end:
        payload = {
            "fullframe": False,
            "timestamp": datetime.datetime.strftime(current_time, "%Y-%m-%dT%H:%M:00Z")
        }

        headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Cisco-Meraki-API-Key": apikey
        }

        response = requests.request('POST', snapshot_url, headers=headers, data = json.dumps(payload))
        print(response.status_code)
        response = response.text
        try:
            img = json.loads(response)
            print(img)
            url = img['url']

            resp = requests.get(url, verify=False)
            with open(f"./snapshots/snapshot{i}.png", "wb") as f:
                while resp.status_code != 200:
                    time.sleep(2)
                    resp = requests.get(url, verify=False)
                f.write(resp.content)
                f.close()
                i += 1
        except Exception as e:
            print(e)
            print("Failed snapshot")

        current_time = current_time + datetime.timedelta(minutes = int(interval))
        print(current_time)
    
    return i

# Creates a GIF from the snapshots in the 'snapshots' folder
def make_gif(nb_snapshots):
    images = []
    filenames = []
    for i in range(nb_snapshots):
        filenames += [f"./snapshots/snapshot{i}.png"]
    for filename in filenames:
        images.append(imageio.imread(filename))
    imageio.mimsave('./snapshots/timelapse.gif', images)

if __name__ == '__main__':
    load_dotenv()
    app.run(port=5004,debug=True)
    