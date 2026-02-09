import domoticz
import configuration
from adapter import UniversalAdapter

class DevicesManager:
    def __init__(self):
        self.devices = {}

    def add_devices(self, wifisensors_devices):
        for item in wifisensors_devices:
            device_adress = item['ieee_address']            
            self.devices[device_adress] = UniversalAdapter(item)
            self.devices[device_adress].register()

    def get_device_by_name(self, name):
        for key, adapter in self.devices.items():
            if adapter.wifisensors_device['ieee_address'] == name:
                return adapter

    def handle_command(self, device_id, unit, command, level, color):
        try:
            domoticz_device = domoticz.get_device(device_id, unit)
            config = configuration.get_wifisensors_feature_data(device_id, unit)
            
            alias = config['domoticz']['legacy_alias']
            device_address = config['wifisensors']['address']
            adapter = self.devices[device_address]
        except:
            return

        return adapter.handle_command(alias, domoticz_device, command, level, color)

