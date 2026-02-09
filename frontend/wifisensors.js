define([
    'app',
    '../templates/wifisensors/viz',
    '../templates/wifisensors/viz.full.render',
    '../templates/wifisensors/leaflet',
    '../templates/wifisensors/plugin_config',
    '../templates/wifisensors/wifisensors_devices',
    '../templates/wifisensors/wifisensors_health',
    'app/devices/Devices.js'
],
function(app, Viz, vizRenderer, leaflet) {
    var viz = new Viz(vizRenderer);

    app.component('wifisensorsPlugin', {
        templateUrl: 'app/wifisensors/index.html',
        controller: wifisensorsPluginController
    });

    // Allows to load Devices.html which contains templates for <devices-table /> component
    app.component('wifisensorsFakeDevices', {
        templateUrl: 'app/devices/Devices.html',
    });

    app.factory('wifisensors', function($q, $rootScope, domoticzApi) {
        var requestsCount = 0;
        var requestsQueue = [];
        var deviceIdxDefer = $q.defer();
        var commandsQueue = $q.resolve();

        $rootScope.$on('device_update', function(e, device) {
            getControlDeviceIndex().then(function(deviceIdx) {
                if (device.idx === deviceIdx) {
                    handleResponse(JSON.parse(device.Data))
                }
            })
        });

        return {
            setControlDeviceIdx: setControlDeviceIdx,
            sendRequest: sendRequest,
        };

        function setControlDeviceIdx(idx) {
            deviceIdxDefer.resolve(idx);
            
            // In case idx was already resolved before
            deviceIdxDefer = $q.defer();
            deviceIdxDefer.resolve(idx);
        }

        function getControlDeviceIndex() {
            return deviceIdxDefer.promise;
        }

        function sendRequest(command, params) {
            return getControlDeviceIndex().then(function(deviceIdx) {
                function sendDomoticzRequest() {
                    var deferred = $q.defer();
                    var requestId = ++requestsCount;
        
                    var requestInfo = {
                        requestId: requestId,
                        deferred: deferred,
                    };
        
                    requestsQueue.push(requestInfo);
    
                    domoticzApi.sendCommand('udevice', {
                        idx: deviceIdx,
                        svalue: JSON.stringify({
                            type: 'request',
                            requestId: requestId,
                            command: command,
                            params: params || {}
                        })
                    }).catch(function(error) {
                        deferred.reject(error);
                    });
    
                    return deferred.promise;
                }

                commandsQueue = commandsQueue.then(sendDomoticzRequest, sendDomoticzRequest)
                return commandsQueue;
            });
        }

        function handleResponse(data) {
            if (data.type !== 'response' && data.type !== 'status') {
                return;
            }

            var requestIndex = requestsQueue.findIndex(function(item) {
                return item.requestId === data.requestId;
            });

            if (requestIndex === -1) {
                return;
            }

            var requestInfo = requestsQueue[requestIndex];

            if (data.type === 'status') {
                requestInfo.deferred.notify(data.payload);
                return;
            }

            if (data.isError) {
                requestInfo.deferred.reject(data.payload);
            } else {
                requestInfo.deferred.resolve(data.payload);
            }

            requestsQueue.splice(requestIndex, 1);
        }
    });

    function wifisensorsPluginController($element, $scope, Device, domoticzApi, dzNotification, wifisensors) {
        var $ctrl = this;

        $ctrl.selectPlugin = selectPlugin;
        $ctrl.getVersionString = getVersionString;
        $ctrl.fetchwifisensorsDevices = fetchwifisensorsDevices;
        $ctrl.refreshDomoticzDevices = refreshDomoticzDevices;

        $ctrl.$onInit = function() {
            $ctrl.selectedApiDeviceIdx = null;
            $ctrl.devices = [];

            refreshDomoticzDevices().then(function() {
                $ctrl.pluginApiDevices = $ctrl.devices.filter(function(device) {
                    return device.Unit === 255
                });

                if ($ctrl.pluginApiDevices.length > 0) {
                    $ctrl.selectPlugin($ctrl.pluginApiDevices[0].idx);
                }
            });

            $scope.$on('device_update', function(event, deviceData) {
                var device = $ctrl.devices.find(function(device) {
                    return device.idx === deviceData.idx && device.Type === deviceData.Type;
                });

                if (device) {
                    Object.assign(device, deviceData);
                }
            });
        };

        function selectPlugin(apiDeviceIdx) {
            $ctrl.selectedApiDeviceIdx = apiDeviceIdx;
            wifisensors.setControlDeviceIdx(apiDeviceIdx);

            $ctrl.controllerInfo = null;
            $ctrl.pluginInfo = null;
            $ctrl.wifiDevices = null;

            fetchControllerInfo();
            fetchPluginInfo();
            fetchwifisensorsDevices();
        }

        function fetchwifisensorsDevices() {
            return wifisensors.sendRequest('devices_get').then(function(devices) {
                $ctrl.wifiDevices = devices.map(function(device) {
                    return Object.assign({
                        type: 'N/A'
                    }, device);
                }).sort(function(a, b) {
                    return a.name < b.name ? -1 : 1
                });
            });
        }

        function fetchControllerInfo() {
            return wifisensors.sendRequest('bridge_getstatus').then(function(data) {
                $ctrl.controllerInfo = data;
            });
        }

        function fetchPluginInfo() {
            return wifisensors.sendRequest('plugin_info').then(function(data) {
                $ctrl.pluginInfo = data;
            });
        }

        function getVersionString() {
            var wifisensors = `v.${$ctrl.controllerInfo.version} (${$ctrl.controllerInfo.mac})`;
            var plugin = `v.${$ctrl.pluginInfo.Version}`            
            return `plugin: ${plugin}, wifisensors: ${wifisensors}`;
        }

        function refreshDomoticzDevices() {
            return domoticzApi.sendRequest({
                type: 'command',
                param: 'getdevices',
                displayhidden: 1,
                filter: 'all',
                used: 'all'
            })
                .then(domoticzApi.errorHandler)
                .then(function(response) {
                    if (response.result !== undefined) {
                        $ctrl.devices = response.result
                            .filter(function(device) {
                                return device.HardwareType === 'WifiSensors'
                            })
                            .map(function(device) {
                                return new Device(device)
                            });
                    } else {
                        $ctrl.devices = [];
                    }
                });
        }
    }
});