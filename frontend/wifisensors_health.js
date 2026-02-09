define(['app', 'ace', 'ace-language-tools'], function(app) {
    app.component('wifisensorsHealth', {
        templateUrl: 'app/wifisensors/wifisensorsHealth.html',
        controller: wifisensorsHealthController
    })

    function wifisensorsHealthController($scope, $element, bootbox, wifisensors) {
        var $ctrl = this;
        var aceEditor;

        $ctrl.isModified = false;
        $ctrl.$onInit = function() {
            fetchConfig();
        }

        function fetchConfig() {
            return wifisensors.sendRequest('health_get').then(function(config) {
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
            }).catch(function() {
                bootbox.alert('Failed to load health');
            })
        }
    }
});