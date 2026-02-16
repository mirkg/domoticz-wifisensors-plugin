
import requests
import domoticz
import traceback
from time import time

health = {}
devices = {}
values = {}

def get_health():
    global health
    return health

def get_devices():
    global devices
    devs =[]
    for d in list(devices.values()):
        devs.append(d.to_json())
    return devs

class Wifisensors:

    last_update = 0
    ieee = ''

    def __init__(self, baseurl, headers, interval, devices_manager, track_signal, track_memory):
        self.baseurl = baseurl
        self.headers = headers
        self.interval = interval
        self.devices_manager = devices_manager
        self.track_signal = track_signal
        self.track_memory = track_memory

    def create_internal_devices(self):
        if self.track_signal:
            d = {'id':'251', 'type':'numeric', 'definition':{'exposes': [{'type':'numeric', 'name':'linkquality', 'property':'linkquality'}]}}
            self.signal_dev = self.create_domoticz_dev(d)
        else:
            self.signal_dev = None

        if self.track_memory:
            d = {'id':'252', 'type':'numeric', 'definition':{'exposes': [{'type':'numeric', 'name':'memory', 'property':'memory'}]}}
            self.memory_dev = self.create_domoticz_dev(d)
        else: 
            self.track_memory = None
        
        d = {'id':'253', 'type':'text', 'definition':{'exposes': [{'type':'text', 'name':'warnings', 'property':'warnings'}]}}
        self.warnings_dev = self.create_domoticz_dev(d)

        d = {'id':'254', 'type':'text', 'definition':{'exposes': [{'type':'text', 'name':'connected', 'property':'connected'}]}}
        self.connected_dev = self.create_domoticz_dev(d)

    def run_request(self, path, method="get", payload=None, timeout=3, retry=3) -> dict:        
        while retry > -1:
            try:
                if method == "get":
                    r = requests.get(self.baseurl + path, headers=self.headers, timeout=timeout)
                elif method == "post":
                    r = requests.post(self.baseurl + path, data=payload, headers=self.headers, timeout=timeout)
                elif method == "delete":
                    r = requests.delete(self.baseurl + path, data=payload, headers=self.headers, timeout=timeout)
                j = r.json()
                return j
            except Exception as ex:
                cname = ex.__class__.__name__
                if cname == "ReadTimeout" or cname == "ConnectTimeout":
                    retry -= 1
                    if retry < 0:
                        raise(ex)
                else:
                    raise(ex)

    def check_updates(self):
        global health
        now = int(time())
        if self.last_update + self.interval < now:
            try:
                self.last_update = now
                health = self.run_request('/status')
                if self.ieee == '':
                    self.set_ieee(health)
                    self.create_internal_devices()
                self.update_stats(health)
            except Exception:
                domoticz.error('check status failed: ' + traceback.format_exc())
            self.update_devices()
            try:
                self.last_update = now
                self.map_values(self.run_request('/'))
                self.update_values()
            except Exception:
                domoticz.error('get values failed: ' + traceback.format_exc())

    def map_device_definition(self, dev):
        expo = []
        
        if 'GENERIC_ANALOG' == dev['type']:
            expo.append({'type':'numeric', 'name':'generic_analog', 'property': list(dev['units'].keys())[0]})
        elif 'GENERIC_DIGITAL' == dev['type']:
            expo.append({'type':'numeric', 'name':'generic_digital', 'property': list(dev['units'].keys())[0]})
        elif 'DHT22' == dev['type']:
            expo.append({'type':'numeric', 'name':'temp+hum', 'property': list(dev['units'].keys())[0]})
        elif 'TEMP_DALLAS' == dev['type']:
            expo.append({'type':'numeric', 'name':'temperature', 'property': list(dev['units'].keys())[0]})
        elif 'MOTION' == dev['type']:
            expo.append({'type':'binary', 'name':'state', 'property': list(dev['units'].keys())[0]})
        elif 'BUTTON' == dev['type']:
            expo.append({'type':'binary', 'name':'state', 'property': list(dev['units'].keys())[0]})
        elif 'RELAY' == dev['type']:
            expo.append({'type':'binary', 'name':'state', 'property': list(dev['units'].keys())[0]})
        elif 'SWITCH' == dev['type']:
            expo.append({'type':'binary', 'name':'state', 'property': list(dev['units'].keys())[0]})

        defs = {'exposes': expo}
        return defs

    def map_values(self, data):
        global values
        if 'values' in data:
            values = data['values']
            for k in values:
                if k in devices:
                    values[k]['raw'] = {}
                    values[k]['nValue'] = 0
                    dtype = devices[k].to_json()['type']
                    if dtype == 'DHT22':
                        values[k]['sValue'] = str(values[k]['temp']) + ";" + str(values[k]['humid']) + ";0"
                    elif dtype == 'TEMP_DALLAS':
                        values[k]['sValue'] = str(values[k]['temp'])
                    elif dtype == 'MOTION' or dtype == 'BUTTON' or dtype == 'RELAY' or dtype == 'SWITCH':
                        values[k]['sValue'] = str(values[k]['state'])
                    else:
                        values[k]['sValue'] = str(values[k]['value'])

    def set_ieee(self, health):
        self.ieee = '0x' + health['mac'].replace(':', '')

    def update_stats(self, health):
        try:
            if self.warnings_dev != None:
                val = {'raw':{}, 'nValue':0, 'sValue':health['last_warn']}
                self.warnings_dev.devices[0].handle_message(self.warnings_dev.to_json(), val)
            if self.connected_dev != None:
                val = {'raw':{}, 'nValue':0, 'sValue':health['connected']}
                self.connected_dev.devices[0].handle_message(self.connected_dev.to_json(), val)
            if self.signal_dev != None:
                val = {'raw':{}, 'nValue':0, 'sValue':str(health['rssi'])}
                self.signal_dev.devices[0].handle_message(self.signal_dev.to_json(), val)
            if self.memory_dev != None:
                val = {'raw':{}, 'nValue':0, 'sValue':str(health['memory'])}
                self.memory_dev.devices[0].handle_message(self.memory_dev.to_json(), val)
        except Exception as ex:
            domoticz.debug(str(ex))

    def update_devices(self):
        global devices
        global values
        refreshDevices = False
        for k in values.keys():
            if not k in devices:
                refreshDevices = True
        if refreshDevices and not self.ieee == '':
            devs = self.run_request('/devices')
            for d in devs['devices']:
                del d['values']
                if not d['id'] in devices.keys():
                    d['definition'] = self.map_device_definition(d)
                    self.create_domoticz_dev(d)
                    devices[d['id']] = self.devices_manager.get_device_by_name(self.ieee + '_' + str(d['id']))

    def update_values(self):
        global devices
        global values
        for k in values:
            if k in devices:
                for dev in devices[k].devices:
                    dev.handle_message(devices[k].to_json(), values[k])

    def create_domoticz_dev(self, dev):
        wifisensors_device = dev
        wifisensors_device['ieee_address'] = self.ieee + '_' + str(dev['id'])        
        domoticz.debug('creating device: ' + str(wifisensors_device))
        self.devices_manager.add_devices([wifisensors_device])
        return self.devices_manager.get_device_by_name(self.ieee + '_' + str(dev['id']))
