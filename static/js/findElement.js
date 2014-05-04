'use strict';

oml.ui.findElement = function() {

    var ui = oml.user.ui,
    	findIndex = ui._findState.index,
        findKey = ui._findState.key,
        findValue = ui._findState.value,
        hasPressedClear = false,
        previousFindKey = findKey,

       	that = Ox.FormElementGroup({

       		elements: [

   				oml.$ui.findScopeSelect = renderFindScopeSelect(),

   				oml.$ui.findSelect = Ox.Select({
                    id: 'select',
                    items: [].concat(
                        oml.config.findKeys.map(function(key) {
                            return {
                                id: key.id,
                                title: Ox._('Find: {0}', [Ox._(key.title)])
                            };
                        }),
                        [{}, {
                            id: 'advanced',
                            title: Ox._('Find: Advanced...')
                        }]
                    ),
                    overlap: 'right',
                    style: 'squared',
                    value: findKey,
                    width: 160
                })
                .bindEvent({
                    change: function(data) {
                        if (data.value == 'advanced') {
                            that.updateElement();
                            //oml.$ui.mainMenu.checkItem('findMenu_find_' + previousFindKey);
                            oml.$ui.filterDialog = oml.ui.filterDialog().open();
                        } else {
                            //oml.$ui.mainMenu.checkItem('findMenu_find_' + data.value);
                            oml.$ui.findInput.options({
                                autocomplete: getAutocomplete(),
                                placeholder: ''
                            }).focusInput(true);
                            previousFindKey = data.value;
                        }
                    }
                }),

                oml.$ui.findInput = Ox.Input({
                    autocomplete: getAutocomplete(),
                    autocompleteSelect: true,
                    autocompleteSelectHighlight: true,
                    autocompleteSelectMaxWidth: 256,
                    autocompleteSelectSubmit: true,
                    clear: true,
                    clearTooltip: Ox._('Click to clear or doubleclick to reset query'),
                    id: 'input',
                    placeholder: findKey == 'advanced' ? Ox._('Edit Query...') : '',
                    style: 'squared',
                    value: findValue,
                    width: 240
                })
                .bindEvent({
                    clear: function() {
                        hasPressedClear = true;
                    },
                    focus: function(data) {
                        if (oml.$ui.findSelect.value() == 'advanced') {
                            if (hasPressedClear) {
                                oml.UI.set({find: oml.site.user.ui.find});
                                that.updateElement();
                                hasPressedClear = false;
                            }
                            oml.$ui.findInput.blurInput();
                            oml.$ui.filterDialog = oml.ui.filterDialog().open();
                        }
                    },
                    submit: function(data) {
                        var scope = oml.$ui.findScopeSelect.value(),
                            key = oml.$ui.findSelect.value(),
                            conditions = [].concat(
                                scope == 'list' ? [{
                                    key: 'list',
                                    value: ui._list,
                                    operator: '=='
                                }] : [],
                                scope == 'user' ? [{
                                    key: 'list',
                                    value: ui._list.split(':')[0],
                                    operator: '=='
                                }] : [],
                                data.value ? [{
                                    key: key,
                                    value: data.value,
                                    operator: '='
                                }] : []
                            );
                        oml.UI.set({
                        	find: {
                        		conditions: conditions,
                        		operator: '&'
                        	}
                       	});
                    }
                })

       		]
       	})
		.css({
			float: 'right',
			margin: '4px 4px 4px 2px'
		})
        .bindEvent({
            oml_find: function() {
                that.replaceElement(
                    0, oml.$ui.findScopeSelect = renderFindScopeSelect()
                );
            }
        });

    function getAutocomplete() {
        var key = !that
                ? ui._findState.key
                : that.value()[ui._list ? 1 : 0],
            findKey = Ox.getObjectById(oml.config.findKeys, key);
        return findKey && findKey.autocomplete ? function(value, callback) {
            oml.api.autocomplete({
                key: key,
                query: {
                    conditions: ui._list
                    	&& oml.$ui.findScopeSelect.value() == 'list'
                        ? [{
                        	key: 'list',
                        	operator: '==',
                        	value: ui._list
                        }]
                        : [],
                    operator: '&'
                },
                range: [0, 20],
                sort: findKey.autocompleteSort,
                value: value
            }, function(result) {
                callback(result.data.items.map(function(item) {
                    return Ox.decodeHTMLEntities(item);
                }));
            });
        } : null;
    }

    function renderFindScopeSelect() {
        var scope = !ui._list ? 'all'
            : Ox.endsWith(ui._list, ':') ? 'user'
            : 'list';
        return Ox.Select({
                items: [
                    {id: 'all', title: Ox._('Find: All Libraries')},
                ].concat(scope != 'all' ? [
                    {id: 'user', title: Ox._('Find: This Library')},
                ] : []).concat(scope == 'list' ? [
                    {id: 'list', title: Ox._('Find: This List')}
                ] : []),
                overlap: 'right',
                style: 'squared',
                title: scope == 'all' ? 'data' : scope,
                type: 'image',
                tooltip: Ox._('Find: FIXME'),
                value: scope
            })
            .bindEvent({
                change: function(data) {
                    oml.$ui.findScopeSelect.options({
                        title: data.value == 'all' ? 'data' : data.value,
                        tooltip: data.title
                    });
                    oml.$ui.findInput.focusInput(true);
                }
            });
    }

    that.updateElement = function() {
        var findState = ui._findState;
        oml.$ui.findSelect.value(findState.key);
        oml.$ui.findInput.options(
            findState.key == 'advanced' ? {
                placeholder: Ox._('Edit Query...'),
                value: ''
            } : {
                autocomplete: getAutocomplete(),
                placeholder: '',
                value: findState.value
            }
        );
    };

    return that;

};