"""
<plugin key="WifiSensors" name="WifiSensors" version="0.1.0">
    <description>
        <h2>WifiSensors Plugin</h2>
        <p>Plugin to add support for <a href="https://github.com/mirkg/arduino-WifiSensors"> WifiSensors </a> project</p>
    </description>
    <params>
        <param field="Address" label="WifiSensors server address" width="300px" required="true" default="127.0.0.1"/>
        <param field="Port" label="WifiSensors server Port" width="300px" required="true" default="80"/>
        <param field="Username" label="Basic Auth Username (optional)" width="300px" required="false" default=""/>
        <param field="Password" label="Basic Auth Password (optional)" width="300px" required="false" default="" password="true"/>
        <param field="Mode1" label="Track Wifi Signal Quality" width="300px">
            <options>
                <option label="Yes" value="Yes" default="true"/>
                <option label="No" value="No" />
            </options>
        </param>
        <param field="Mode2" label="Track Memory Usage" width="300px">
            <options>
                <option label="Yes" value="Yes" default="true"/>
                <option label="No" value="No" />
            </options>
        </param>
        <param field="Mode3" label="Debug" width="75px">
            <options>
                <option label="Verbose" value="Verbose"/>
                <option label="True" value="Debug"/>
                <option label="False" value="Normal" default="true" />
            </options>
        </param>
    </params>
</plugin>
"""

import DomoticzEx as Domoticz
import domoticz
import os
from shutil import copy2, rmtree
from base64 import b64encode
from api import API
import configuration
from wifisensors import Wifisensors
from devices_manager import DevicesManager

class BasePlugin:

    def onStart(self):
        self.debugging = Parameters["Mode3"]
        
        if self.debugging == "Verbose":
            Domoticz.Debugging(2+4+8+16+64)
        if self.debugging == "Debug":
            Domoticz.Debugging(2)

        self.install()
        self.track_signal = Parameters["Mode1"].strip().lower() == 'yes'
        self.track_memory = Parameters["Mode2"].strip().lower() == 'yes'

        self.server_address = Parameters["Address"].strip()
        self.server_port = Parameters["Port"].strip()

        if not self.server_address.startswith('http'):
            if self.server_port == '443':
                self.server_address = "https://" + self.server_address
            else:
                self.server_address = "http://" + self.server_address

        self.api = API(self.onApiCommand)
        self.devices_manager = DevicesManager()

        self.headers = {'Authorization':'Basic ' + b64encode(f"{Parameters["Username"]}:{Parameters["Password"]}".encode('utf-8')).decode("ascii")}
        self.wifisensors = Wifisensors(self.server_address + ":" + self.server_port, self.headers, 60, self.devices_manager, self.track_signal, self.track_memory)

    def checkDevices(self):
        domoticz.debug("checkDevices called")

    def onStop(self):
        domoticz.debug("onStop called")
        self.uninstall()

    def onCommand(self, device_id, unit, command, Level, Color):
        domoticz.debug("[Command] Device " + device_id + '(' + str(unit) + '): ' + command + "(level = " + str(Level) + ", color = " + Color + ')')

        message = None
        domoticz_device = domoticz.get_device(device_id, unit)
        wifisensors_device_alias = configuration.get_wifisensors_feature_data(device_id, unit)
        
        if wifisensors_device_alias == None:
            domoticz.log('Can not process command from device "' + domoticz_device.Name + '"')

        message = self.devices_manager.handle_command(device_id, unit, command, Level, Color)

        if (message != None):
            #TODO
            domoticz.log('process command from device "' + str(message) + '"')

    def onApiCommand(self, command, data):
        domoticz.error('Internal API command "' + command +'" is not supported by plugin')

    def onConnect(self, Connection, Status, Description):
        domoticz.debug("onConnect called for connection to: "+ Connection.Address + ":" + Connection.Port)

    def onDisconnect(self, Connection):
        domoticz.debug("onDisconnect called for connection to: " + Connection.Address + ":" + Connection.Port)

    def onDeviceModified(self, device_id, unit):
        domoticz.debug("onDeviceModified : " + device_id)
        if device_id == 'api_transport' and unit == 255:
            device = domoticz.get_device(device_id, unit)
            self.api.handle_request(device.sValue)
            return

    def onDeviceRemoved(self, device_id, unit):
        domoticz.debug("onDeviceRemoved : " + device_id)

    def onMessage(self, Connection, Data):
        domoticz.debug("onMessage called for connection to: " + Connection.Address + ":" + Connection.Port)
        DumpHTTPResponseToLog(Data)

    def onTimeout(self, Connection):
        domoticz.debug("onTimeout called for connection to: " + Connection.Address + ":" + Connection.Port)

    def onHeartbeat(self):
        domoticz.debug("onHeartbeat called, Connection is alive.")
        self.wifisensors.check_updates()

    def install(self):
        domoticz.log('Installing plugin custom page...')

        try:
            source_path = Parameters['HomeFolder'] + 'frontend'
            templates_path = Parameters['StartupFolder'] + 'www/templates'
            dst_plugin_path = templates_path + '/wifisensors'

            domoticz.debug('Copying files from ' + source_path + ' to ' + templates_path)

            if not (os.path.isdir(dst_plugin_path)):
                os.makedirs(dst_plugin_path)

            copy2(source_path + '/wifisensors.html', templates_path)
            copy2(source_path + '/wifisensors.js', templates_path)
            copy2(source_path + '/wifisensors_devices.js', dst_plugin_path)
            copy2(source_path + '/wifisensors_health.js', dst_plugin_path)
            copy2(source_path + '/plugin_config.js', dst_plugin_path)
            copy2(source_path + '/libs/leaflet.js', dst_plugin_path)
            copy2(source_path + '/libs/leaflet.css', dst_plugin_path)
            copy2(source_path + '/libs/viz.js', dst_plugin_path)
            copy2(source_path + '/libs/viz.full.render.js', dst_plugin_path)
            copy2(source_path + '/libs/ace_json_mode.js', dst_plugin_path)
            copy2(source_path + '/libs/ace_worker_json.js', dst_plugin_path)
            
            domoticz.log('Installing plugin custom page completed.')
        except Exception as e:
            domoticz.error('Error during installing plugin custom page')
            domoticz.error(repr(e))

    def uninstall(self):
        domoticz.log('Uninstalling plugin custom page...')

        try:
            templates_path = Parameters['StartupFolder'] + 'www/templates'
            dst_plugin_path = templates_path + '/wifisensors'

            domoticz.debug('Removing files from ' + templates_path)

            if (os.path.isdir(dst_plugin_path)):
                rmtree(dst_plugin_path)

            if os.path.exists(templates_path + "/wifisensors.html"):
                os.remove(templates_path + "/wifisensors.html")

            if os.path.exists(templates_path + "/wifisensors.js"):
                os.remove(templates_path + "/wifisensors.js")

            domoticz.log('Uninstalling plugin custom page completed.')
        except Exception as e:
            domoticz.error('Error during uninstalling plugin custom page')
            domoticz.error(repr(e))


global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()
    
def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onDeviceModified(DeviceId, Unit):
    global _plugin
    _plugin.onDeviceModified(DeviceId, Unit)

def onDeviceRemoved(DeviceId, Unit):
    global _plugin
    _plugin.onDeviceRemoved(DeviceId, Unit)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)

def onCommand(DeviceId, Unit, Command, Level, Color):
    global _plugin
    _plugin.onCommand(DeviceId, Unit, Command, Level, Color)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

def DumpHTTPResponseToLog(httpResp, level=0):
    if (level==0): Domoticz.Debug("HTTP Details ("+str(len(httpResp))+"):")
    indentStr = ""
    for x in range(level):
        indentStr += "----"
    if isinstance(httpResp, dict):
        for x in httpResp:
            if not isinstance(httpResp[x], dict) and not isinstance(httpResp[x], list):
                Domoticz.Debug(indentStr + ">'" + x + "':'" + str(httpResp[x]) + "'")
            else:
                Domoticz.Debug(indentStr + ">'" + x + "':")
                DumpHTTPResponseToLog(httpResp[x], level+1)
    elif isinstance(httpResp, list):
        for x in httpResp:
            Domoticz.Debug(indentStr + "['" + x + "']")
    else:
        Domoticz.Debug(indentStr + ">'" + x + "':'" + str(httpResp[x]) + "'")
