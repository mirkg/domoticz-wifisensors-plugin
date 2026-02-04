import json
import domoticz
from adapters.base_adapter import Adapter
from devices.on_off_switch import OnOffSwitch
from devices.custom_sensor import CustomSensor
from devices.on_off_switch import OnOffSwitch
from devices.temperature_humidity_sensor import TemperatureHumiditySensor
from devices.temperature import TemperatureSensor
from devices.text_sensor import TextSensor

class UniversalAdapter(Adapter):
    def __init__(self, wifisensors_device):
        self.devices = []
        self.name = wifisensors_device['type']
        wifisensors_device['name'] = self.name
        self.wifisensors_device = wifisensors_device
        
        if 'exposes' not in wifisensors_device['definition']:
            domoticz.error(self.name + ': device exposes not found')
            return

        self._add_features(wifisensors_device['definition']['exposes'])
        self.register()

    def _add_features(self, features):
        for item in features:
            if 'name' in item and item['name'] in ['energy', 'power', 'temperature', 'humidity', 'pressure']:
                continue
            else:
                self._add_feature(item)

    def _add_feature(self, item):
        if item['type'] == 'binary':
            self.add_binary_device(item)
        elif item['type'] == 'numeric':
            self.add_numeric_device(item)
        elif item['type'] == 'text':
            self.add_text_device(item)
        elif item['type'] == 'switch':
            self._add_features(item['features'])
        else:
            domoticz.debug(self.name + ': can not process feature type "' + item['type'] + '"')
            domoticz.debug(json.dumps(item))

    def _add_device(self, alias, feature, device_type, device_name_suffix = ''):
        suffix = device_name_suffix
        device = device_type(alias, feature['property'], suffix)
        device.feature = feature

        self.devices.append(device)
        return device

    def _get_feature(self, features, feature_name):
        for item in features:
            if 'name' in item and item['name'] == feature_name:
                return item

        return False

    def _has_access(self, access, access_type):
        mask = 1 << access_type
        return bool(access & mask)

    def _generate_alias(self, feature, default_value):
        if 'endpoint' in feature:
            return feature['endpoint']
        else:
            return default_value

    def add_binary_device(self, feature):
        if (feature['name'] == 'state'):
            alias = self._generate_alias(feature, 'state')
            self._add_device(alias, feature, OnOffSwitch)
            return

        domoticz.debug(self.name + ': can not process binary item "' + feature['name'] + '"')
        domoticz.debug(json.dumps(feature))

    def add_numeric_device(self, feature):
        if (feature['name'] == 'linkquality'):
            self._add_device('signal', feature, CustomSensor)
            return
        if (feature['name'] == 'memory'):
            self._add_device('memory', feature, CustomSensor)
            return
        if (feature['name'] == 'generic_analog'):
            alias = self._generate_alias(feature, 'analog')
            self._add_device(alias, feature, CustomSensor)
            return
        if (feature['name'] == 'generic_digital'):
            alias = self._generate_alias(feature, 'digital')
            self._add_device(alias, feature, CustomSensor)
            return
        if (feature['name'] == 'temp+hum'):
            alias = self._generate_alias(feature, 'Temp + Humidity')
            self._add_device(alias, feature, TemperatureHumiditySensor)
            return
        if (feature['name'] == 'temperature'):
            alias = self._generate_alias(feature, 'Temp')
            self._add_device(alias, feature, TemperatureSensor)
            return        
        
        domoticz.debug(self.name + ': can not process numeric item "' + feature['name'] + '"')
        domoticz.debug(json.dumps(feature))

    def add_text_device(self, feature):
        domoticz.debug('add_text_device: ' + str(feature))
        if (feature['name'] == 'warnings'):
            alias = self._generate_alias(feature, 'warnings')
            self._add_device(alias, feature, TextSensor)
            return
        if (feature['name'] == 'connected'):
            alias = self._generate_alias(feature, 'connected')
            self._add_device(alias, feature, TextSensor)
            return

        domoticz.debug(self.name + ': can not process binary item "' + feature['name'] + '"')
        domoticz.debug(json.dumps(feature))

    def handle_command(self, alias, domoticz_device, command, level, color):
        device = self.get_device_by_alias(alias)

        if (device == None) :
            return

        feature = device.feature

        # Optimistic update
        device_data = self._get_legacy_device_data()
        device.handle_command(device_data, command, level, color)

        if (feature['type'] == 'binary'):
            topic = self.name + '/' + ((feature['endpoint'] + '/set') if 'endpoint' in feature else 'set')
            key = feature['property']
            value = feature['value_on'] if command.upper() == 'ON' else feature['value_off']
                
            return {
                'topic': topic,
                'payload': json.dumps({
                    key: value
                })
            }

        return None
    
    def to_json(self):
        return self.wifisensors_device

