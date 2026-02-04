define(['app', 'app/devices/Devices.js'], function(app) {

    app.component('wifiDevices', {
        bindings: {
            wifiDevices: '<',
            domoticzDevices: '<',
            onUpdate: '&',
            onUpdateDomoticzDevice: '&',
        },
        templateUrl: 'app/wifisensors/devices.html',
        controller: WifiSensorsDevicesController
    });

    app.component('wifiDevicesTable', {
        bindings: {
            devices: '<',
            onSelect: '&',
            onUpdate: '&'
        },
        template: '<table id="wifi-devices" class="display" width="100%"></table>',
        controller: WifiSensorsDevicesTableController,
    });

    function WifiSensorsDevicesController($scope, $uibModal, wifisensors) {
        var $ctrl = this;

        $ctrl.selectWifiSensorsDevice = selectWifiSensorsDevice;

        $ctrl.$onInit = function() {
            $ctrl.associatedDevices = []
        };

        $ctrl.$onChanges = function(changes) {
            if (changes.domoticzDevices) {
                $ctrl.selectWifiSensorsDevice($ctrl.selectedWifiSensorsDevice)
            }
        };

        function selectWifiSensorsDevice(wifiSensorsDevice) {
            $ctrl.selectedWifiSensorsDevice = wifiSensorsDevice;

            if (!wifiSensorsDevice) {
                $ctrl.associatedDevices = []
            } else {
                $ctrl.associatedDevices = $ctrl.domoticzDevices.filter(function(device) {
                    return device.ID.indexOf(wifiSensorsDevice.ieee_address) === 0;
                });
            }
        }
    }

    function WifiSensorsDevicesTableController($element, $scope, $timeout, $uibModal, wifisensors, bootbox, dzSettings, dataTableDefaultSettings) {
        var $ctrl = this;
        var table;

        $ctrl.$onInit = function() {
            table = $element.find('table').dataTable(Object.assign({}, dataTableDefaultSettings, {
                order: [[0, 'asc']],
                columns: [
                    { title: 'Name', data: 'name' },                    
                    { title: 'Type', width: '150px', data: 'type' },
                    { title: 'IEEE Address', width: '170px', data: 'ieee_address' },
                    { title: 'Pins', data: 'pins', render: jsonRenderer},
                    { title: 'Interval', data: 'poll' },
                    { title: 'Config', data: 'config', render: jsonRenderer},
                    { title: 'Units', data: 'units', render: jsonRenderer},
                ],
            }));

            table.on('select.dt', function(event, row) {
                $ctrl.onSelect({ device: row.data() });
                $scope.$apply();
            });

            table.on('deselect.dt', function() {
                //Timeout to prevent flickering when we select another item in the table
                $timeout(function() {
                    if (table.api().rows({ selected: true }).count() > 0) {
                        return;
                    }

                    $ctrl.onSelect({ device: null });
                });

                $scope.$apply();
            });

            render($ctrl.devices);
        };

        $ctrl.$onChanges = function(changes) {
            if (changes.devices) {
                render($ctrl.devices);
            }
        };

        function render(items) {
            if (!table || !items) {
                return;
            }

            table.api().clear();
            table.api().rows
                .add(items)
                .draw();
        }

        function jsonRenderer(data, type, row) {
            return JSON.stringify(data);
        }
    }
});