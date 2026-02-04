from api.command import APICommand
import domoticz
import configuration
import wifisensors
import json


class GetConfig(APICommand):
    def execute(self, params):
        config = configuration.get_config_item()
        self.send_response(config)

class SetConfig(APICommand):
    def execute(self, params):
        try:
            config = json.loads(params)
            configuration.set_config_item(None, config)
            self.send_response('ok')
        except:
            self.send_error('Failed to update configuration')

class GetHealth(APICommand):
    def execute(self, params):    
        health = wifisensors.get_health()
        self.send_response(health)

class GetStatus(APICommand):
    def execute(self, params):    
        health = wifisensors.get_health()
        self.send_response(health)

class Info(APICommand):
    def execute(self, params):
        data = domoticz.get_plugin_parameters()
        self.send_response(data)