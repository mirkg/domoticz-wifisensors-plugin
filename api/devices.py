from api.command import APICommand
import wifisensors

class GetDevices(APICommand):
    def execute(self, params):
        devices = wifisensors.get_devices()
        self.send_response(devices)
