import domoticz
from devices.custom_sensor import CustomSensor


class Adapter():
    def __init__(self):
        self.devices = []

    def convert_message(self, message):
        return message

    def _get_legacy_device_data(self):
        if 'type' not in self.wifisensors_device:
            domoticz.error(self.name + ': device does not contain type')
            return

        return {
            'type': self.wifisensors_device['type'],
            'ieee_address': self.wifisensors_device['ieee_address'],
            'name': self.name
        }

    def register(self):
        for device in self.devices:
            device.register(self._get_legacy_device_data())

    def get_device_by_alias(self, alias):
        for device in self.devices:
            if device.alias == alias:
                return device
        return None

    def handle_command(self, alias, device, command, level, color):
        domoticz.debug('Update command has not been implemented for device "' + device.Name + '"')
