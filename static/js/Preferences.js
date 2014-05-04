'use strict';

oml.Preferences = (function() {

    var that = {};

    that.set = function() {

        var args = Ox.isObject(arguments[0])
                ? args
                : Ox.makeObject([arguments[0], arguments[1]]),
            set = {},
            preferences = oml.user.preferences,
            previousPreferences = Ox.clone(preferences, true);

        Ox.forEach(args, function(value, key) {
            if (!Ox.isEqual(preferences[key], value)) {
                preferences[key] = value;
                set[key] = value;
            }
        });

        if (Ox.len(set)) {
            oml.api.setPreferences(set);
            Ox.forEach(set, function(value, key) {
                Ox.forEach(oml.$ui, function($element) {
                    if (Ox.UI.isElement($element)) {
                        $element.triggerEvent('oml_' + key.toLowerCase(), {
                            value: value,
                            previousValue: previousPreferences[key]
                        });
                    }
                });
            });
        }

    };

    return that;

}());