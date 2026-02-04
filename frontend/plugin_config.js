define(['app', 'ace', 'ace-language-tools'], function(app) {
    app.component('wifisensorsPluginConfig', {
        templateUrl: 'app/wifisensors/wifisensorsPluginConfig.html',
        controller: wifisensorsPluginConfigController
    })

    function wifisensorsPluginConfigController($scope, $element, bootbox, wifisensors) {
        var $ctrl = this;
        var aceEditor;

        $ctrl.isModified = false;
        $ctrl.updateConfig = updateConfig;
        $ctrl.$onInit = function() {
            fetchConfig();
        }

        function fetchConfig() {
            return wifisensors.sendRequest('config_get').then(function(config) {
                $ctrl.config = config;
                
                var element = $element.find('.js-script-content')[0];
                aceEditor = ace.edit(element);

                aceEditor.setOptions({
                    enableBasicAutocompletion: true,
                    enableSnippets: true,
                    enableLiveAutocompletion: true
                });

                ace.config.setModuleUrl("ace/mode/json", "/templates/wifisensors/ace_json_mode.js");
                ace.config.setModuleUrl("ace/mode/json_worker", "/templates/wifisensors/ace_worker_json.js");
                aceEditor.setTheme('ace/theme/xcode');
                aceEditor.setValue(JSON.stringify(config, null, '\t'));
                aceEditor.getSession().setMode('ace/mode/json');
                aceEditor.gotoLine(1);
                aceEditor.scrollToLine(1, true, true);

                aceEditor.on('change', function (event) {
                    $ctrl.isModified = true;
                    $scope.$apply();
                });
            }).catch(function() {
                bootbox.alert('Failed to load plugin configuration');
            })
        }

        function updateConfig() {
            config = aceEditor.getValue()
            
            return wifisensors.sendRequest('config_set', config).then(function() {
                $ctrl.isModified = false;
            }).catch(function() {
                bootbox.alert('Failed to save configuration');
            });
        }
    }
});