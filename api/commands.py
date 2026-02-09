from api.plugin import GetConfig, SetConfig, Info, GetHealth, GetStatus
from api.devices import GetDevices


commands = dict({
    'devices_get': GetDevices,
    'config_get': GetConfig,
    'config_set': SetConfig,
    'health_get': GetHealth,
    'plugin_info': Info,
    'bridge_getstatus': GetStatus
})
