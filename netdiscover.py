import subprocess
import threading
import re
import os
import requests

def get_request(url):
    url = os.environ['ha_url'] + url
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + os.environ['ha_token']
    }
    return requests.request('GET', url, headers=headers)

def post_update(mac, device_id):
    url = os.environ['ha_url'] + '/api/services/device_tracker/see'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + os.environ['ha_token']
    }
    body = {
        'dev_id': device_id,
        'mac': mac,
        'location_name': 'home'
    }
    return requests.request('POST', url, headers=headers, json=body)

def output_reader(proc, monitored):
    seen = {}
    p = re.compile(r'^[ ]*(?P<ip>[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})[ ]+(?P<mac>[0-9A-Za-z]{2}:[0-9A-Za-z]{2}:[0-9A-Za-z]{2}:[0-9A-Za-z]{2}:[0-9A-Za-z]{2}:[0-9A-Za-z]{2})[ ]+(?P<count>[0-9])+[ ]+[0-9]+[ ].*$')

    for line in iter(proc.stdout.readline, b''):
        line = line.decode('utf-8')
        m = p.search(line)
        if m is not None:
            mac = m.group('mac')
            if mac in monitored:
                count = int(m.group('count'))
                prev = seen[mac] if mac in seen else 0
                if count > prev:
                    seen[mac] = count
                    post_update(mac, monitored[mac])
                    print('Saw', monitored[mac], '(' + mac + ')')

if __name__ == "__main__":
    res = get_request('/api/states/group.all_devices')
    devices_ids = res.json()['attributes']['entity_id']
    monitored = {}
    for device_id in devices_ids:
        res = get_request('/api/states/' + device_id)
        attrs = res.json()['attributes']
        if 'mac' in attrs:
            monitored[attrs['mac']] = device_id
        else:
            print('Ignoring', device_id, '- no mac specified in attributes')

    print('Monitoring', len(monitored), 'mac addresses:', monitored)
    proc = subprocess.Popen(['netdiscover', '-i', 'enp32s0', '-p'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    t = threading.Thread(target=output_reader, args=(proc, monitored))
    t.start()
    print('Started netdiscover process')
    t.join()

