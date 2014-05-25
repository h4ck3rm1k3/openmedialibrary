'use strict';

oml.UI = (function() {

    var previousUI = {},
        that = {};

    that.encode = function(value) {
        return value.replace(/\./g, '\\.');
    };

    that.getPrevious = function(key) {
        return !key ? previousUI : previousUI[key];
    };

    that.reset = function() {
        var ui = oml.user.ui;
        oml.api.resetUI({}, function() {
            ui = oml.config.user.ui;
            ui._list = oml.getListState(ui.find);
            ui._filterState = oml.getFilterState(ui.find);
            ui._findState = oml.getFindState(ui.find);
            Ox.Theme(ui.theme);
            oml.$ui.appPanel.reload();
        });
    };

    // sets oml.user.ui.key to value
    // key foo.bar.baz sets oml.user.ui.foo.bar.baz
    // value null removes a key
    that.set = function(/* {key: value}[, flag] or key, value[, flag] */) {

        var add = {},
            args,
            item,
            list,
            listSettings = oml.config.listSettings,
            listView,
            set = {},
            trigger = {},
            triggerEvents,
            ui = oml.user.ui;

        if (Ox.isObject(arguments[0])) {
            args = arguments[0];
            triggerEvents = Ox.isUndefined(arguments[1]) ? true : arguments[1];
        } else {
            args = Ox.makeObject([arguments[0], arguments[1]]);
            triggerEvents = Ox.isUndefined(arguments[2]) ? true : arguments[1];
        }

        Ox.print('UI SET', JSON.stringify(args));

        previousUI = Ox.clone(ui, true);
        previousUI._list = oml.getListState(previousUI.find);

        if ('find' in args) {
            // the challenge here is that find may change list,
            // and list may then change listSort and listView,
            // which we don't want to trigger, since find triggers
            // (values we put in add will be changed, but won't trigger)
            // FIXME: ABOVE COMMENT DOES NOT APPLY
            list = oml.getListState(args.find);
            ui._list = list;
            ui._filterState = oml.getFilterState(args.find);
            ui._findState = oml.getFindState(args.find);
            if (oml.$ui.appPanel && !oml.stayInItemView) {
                // if we're not on page load, and if find isn't a context change
                // caused by an edit, then switch from item view to list view
                args.item = '';
            }
            if (list != previousUI._list) {
                // if find has changed list
                Ox.forEach(listSettings, function(listSetting, setting) {
                    // then for each setting that corresponds to a list setting
                    if (!ui.lists[list]) {
                        // either add the default setting
                        args[setting] = oml.config.user.ui[setting];
                    } else {
                        // or the existing list setting
                        args[setting] = ui.lists[list][listSetting];
                    }
                });
            }
        } else {
            list = previousUI._list;
        }
        // it is important to check for find first, so that
        // if find changes list, list is correct here
        item = args.item || ui.item;
        listView = add.listView || args.listView;

        if (!ui.lists[list]) {
            add['lists.' + that.encode(list)] = {};
        }
        Ox.forEach(listSettings, function(listSetting, setting) {
            // for each setting that corresponds to a list setting
            // set that list setting to
            var key = 'lists.' + that.encode(list) + '.' + listSetting;
            if (setting in args) {
                // the setting passed to UI.set
                args[key] = args[setting];
            } else if (setting in add) {
                // or the setting changed via find
                args[key] = add[setting];
            } else if (!ui.lists[list]) {
                // or the default setting
                args[key] = oml.config.user.ui[setting];
            }
        });

        if (args.item) {
            // when switching to an item, update list selection
            add['listSelection'] = [args.item];
            add['lists.' + that.encode(list) + '.selection'] = [args.item];
            if (
                !args.itemView
                && ui.itemView == 'book'
                && !ui.mediaState[item]
                && !args['mediaState.' + item]
            ) {
                // if the item view doesn't change, remains a media view,
                // media state doesn't exist yet, and won't be set, add
                // default media state
                add['mediaState.' + item] = {position: 0, zoom: 1};
            }
        }

        if (
            args.itemView == 'book'
            && !ui.mediaState[item]
            && !args['mediaState.' + item]
        ) {
            // when switching to a media view, media state doesn't exist
            // yet, and won't be set, add default media state
            add['mediaState.' + item] = {position: 0, zoom: 1};
        }

        // items in args trigger events, items in add do not
        [args, add].forEach(function(object, isAdd) {
            Ox.forEach(object, function(value, key) {
                // make sure to not split at escaped dots ('\.')
                var keys = key.replace(/\\\./g, '\n').split('.').map(function(key) {
                        return key.replace(/\n/g, '.');
                    }),
                    ui_ = ui;
                while (keys.length > 1) {
                    ui_ = ui_[keys.shift()];
                }
                if (!Ox.isEqual(ui_[keys[0]], value)) {
                    if (value === null) {
                        delete ui_[keys[0]];
                    } else {
                        ui_[keys[0]] = value;
                    }
                    set[key] = value;
                    if (!isAdd) {
                        trigger[key] = value;
                    }
                }
            });
        });
        if (Ox.len(set)) {
            oml.api.setUI(set);
        }
        if (triggerEvents) {
            Ox.forEach(trigger, function(value, key) {
                Ox.print('UI TRIGGER', 'oml_' + key.toLowerCase(), value);
                Ox.forEach(oml.$ui, function($elements) {
                    Ox.makeArray($elements).forEach(function($element) {
                        $element.triggerEvent('oml_' + key.toLowerCase(), {
                            value: value,
                            previousValue: previousUI[key]
                        });
                    });
                });
            });
        }
        oml.URL.update(Object.keys(!oml.$ui.appPanel ? args : trigger));

    };

    return that;

}());