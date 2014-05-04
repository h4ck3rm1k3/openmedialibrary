(function() {

    // Note: getFindState has to run after getListState and getFilterState

    function everyCondition(conditions, key, operator) {
        // If every condition has the given key and operator
        // (excluding conditions where all subconditions match)
        // returns true, otherwise false
        return Ox.every(conditions, function(condition) {
            return condition.key == key && condition.operator == operator;
        });
    }

    function oneCondition(conditions, key, operator, includeSubconditions) {
        // If exactly one condition has the given key and operator
        // (including or excluding conditions where all subconditions match)
        // returns the corresponding index, otherwise returns -1
        var indices = Ox.indicesOf(conditions, function(condition) {
            return (
                condition.conditions
                ? includeSubconditions && everyCondition(condition.conditions, key, operator)
                : condition.key == key && condition.operator == operator
            );
        });
        return indices.length == 1 ? indices[0] : -1;
    }


    oml.getFindState = function(find) {
        // The find element is populated if exactly one condition in an & query
        // has a findKey as key and "=" as operator (and all other conditions
        // are either list or filters), or if all conditions in an | query have
        // the same filter id as key and "==" as operator
        Ox.Log('Find', 'getFindState', find)
        // FIXME: this is still incorrect when you select a lot of filter items
        // and reload the page (will be advanced)
        var conditions,
        	indices,
        	state = {index: -1, key: '*', value: ''},
        	ui = oml.user.ui;
        if (find.operator == '&') {
            // number of conditions that are not list or filters
            conditions = find.conditions.length
                - !!ui._list
                - ui._filterState.filter(function(filter) {
                    return filter.index > -1;
                }).length;
            // indices of non-advanced find queries
            indices = oml.config.findKeys.map(function(findKey) {
                return oneCondition(find.conditions, findKey.id, '=');
            }).filter(function(index) {
                return index > -1;
            });
            state = conditions == 1 && indices.length == 1 ? {
                index: indices[0],
                key: find.conditions[indices[0]].key,
                value: Ox.decodeURIComponent(find.conditions[indices[0]].value)
            } : {
                index: -1,
                key: conditions == 0 && indices.length == 0 ? '*' : 'advanced',
                value: ''
            };
        } else {
            state = {
                index: -1,
                key: 'advanced',
                value: ''
            };
            Ox.forEach(ui.filters, function(key) {
                if (everyCondition(find.conditions, key, '==')) {
                    state.key = '*';
                    return false;
                }
            });
        }
        return state;
    }

    oml.getFilterState = function(find) {
        // A filter is selected if exactly one condition in an & query or every
        // condition in an | query has the filter id as key and "==" as operator
	    var ui = oml.user.ui;
        return ui.filters.map(function(filter) {
            // FIXME: cant index be an empty array, instead of -1?
            var key = filter.id,
                state = {index: -1, find: Ox.clone(find, true), selected: []};
            if (find.operator == '&') {
                // include conditions where all subconditions match
                state.index = oneCondition(find.conditions, key, '==', true);
                if (state.index > -1) {
                    state.selected = find.conditions[state.index].conditions
                        ? find.conditions[state.index].conditions.map(function(condition) {
                            return condition.value;
                        })
                        : [find.conditions[state.index].value];
                }
            } else {
                if (everyCondition(find.conditions, key, '==')) {
                    state.index = Ox.range(find.conditions.length);
                    state.selected = find.conditions.map(function(condition) {
                        return condition.value;
                    });
                }
            }
            if (state.selected.length) {
                if (Ox.isArray(state.index)) {
                    // every condition in an | query matches this filter
                    state.find = {conditions: [], operator: ''};
                } else {
                    // one condition in an & query matches this filter
                    state.find.conditions.splice(state.index, 1);
                    if (
                        state.find.conditions.length == 1
                        && state.find.conditions[0].conditions
                    ) {
                        // unwrap single remaining bracketed query
                        state.find = {
                            conditions: state.find.conditions[0].conditions,
                            operator: state.find.conditions[0].operator
                        };
                    }
                }
            }
            return state;
        });
    }

    oml.getListState = function(find) {
        // A list is selected if exactly one condition in an & query has "list"
        // as key and "==" as operator
        var index, state = '';
        if (find.operator == '&') {
            index = oneCondition(find.conditions, 'list', '==');
            if (index > -1) {
                state = find.conditions[index].value;
            }
        }
        return state;
    };

}());

oml.addList = function() {
    // addList(isSmart, isFrom) or addList(list) [=dupicate]
    var args = arguments,
        isDuplicate = args.length == 1,
        isSmart, isFrom, list, listData, data;
    oml.api.getLists(function(result) {
        var lists = result.data.lists,
            listNames = lists[oml.user.id].map(function(list) {
                return list.name;
            }),
            query;
        if (!isDuplicate) {
            isSmart = args[0];
            isFrom = args[1];
            data = {
                name: oml.validateName(Ox._('Untitled'), listNames),
                type: !isSmart ? 'static' : 'smart'
            };
            if (isFrom) {
                if (!isSmart) {
                    data.items = ui.listSelection;
                } else {
                    data.query = ui.find;
                }
            }
            addList();
        } else {
            list = args[0];
            listData = Ox.getObjectById(Ox.flatten(Ox.values(lists)), list);
            Ox.print('LISTDATA,', listData)
            data = Ox.extend({
                name: oml.validateName(listData.name, listNames),
                type: listData.type
            }, listData.query ? {
                query: listData.query
            } : {});
            if (!data.query) {
                var query = {
                    conditions: [{key: 'list', operator: '==', value: list}],
                    operator: '&'
                };
                oml.api.find({query: query}, function(result) {
                    if (result.data.items) {
                        oml.api.find({
                            query: query,
                            keys: ['id'],
                            sort: [{key: 'id', operator: '+'}],
                            range: [0, result.data.items]
                        }, function(result) {
                            data.items = result.data.items.map(function(item) {
                                return item.id;
                            });
                            addList();
                        });
                    } else {
                        addList();
                    }
                });
            } else {
                addList();
            }
        }
    });
    function addList() {
        Ox.print('DATA, ', data);
        oml.api.addList(data, function(result) {
            Ox.print('LIST ADDED', result.data);
            var list = result.data.id,
                $folderList = oml.$ui.folderList[0];
            oml.$ui.folder[0].options({collapsed: false}); // FIXME: SET UI!
            // FIXME: DOESN'T WORK
            $folderList
                .bindEventOnce({
                    load: function() {
                        $folderList
                            .gainFocus()
                            .options({selected: [list]});
                        oml.UI.set({
                            find: {
                                conditions: [{
                                    key: 'list',
                                    operator: '==',
                                    value: list
                                }],
                                operator: '&'
                            }
                        });
                        oml.$ui.listDialog = oml.ui.listDialog().open();
                    }
                });
            oml.updateLists();
        });
    }
};

oml.clearFilters = function() {
    var ui = oml.user.ui,
        find = Ox.clone(ui.find, true),
        indices = ui._filterState.map(function(filterState) {
            return filterState.index;
        }).filter(function(index) {
            return index > -1;
        });
    find.conditions = find.conditions.filter(function(condition, index) {
        return !Ox.contains(indices, index);
    });
    oml.UI.set({find: find});
};

oml.deleteList = function() {
    var ui = oml.user.ui;
    oml.ui.confirmDialog({
        buttons: [
            Ox.Button({
                title: Ox._('No, Keep List')
            }),
            Ox.Button({
                title: Ox._('Yes, Delete List')
            })
        ],
        content: Ox._('Are you sure you want to delete this list?'),
        title: Ox._('Delete List')
    }, function() {
        oml.api.removeList({
            id: ui._list
        }, function() {
            oml.UI.set({
                find: {
                    conditions: [{
                        key: 'list',
                        operator: '==',
                        value: ':'
                    }],
                    operator: '&'
                }
            });
            oml.updateLists();
        });
    });
}

oml.getPageTitle = function(stateOrURL) {
	var page = Ox.getObjectById(
           oml.config.pages,
           Ox.isObject(stateOrURL) ? stateOrURL.page : stateOrURL.slice(1)
        );
	return (page ? page.title + ' – ' : '') + 'Open Media Library';
};

oml.getSortOperator = function(key) {
    var itemKey = Ox.getObjectById(oml.config.itemKeys, key);
    return itemKey.sortOperator
        || Ox.contains(
            ['string', 'text'],
            Ox.isArray(itemKey.type) ? itemKey.type[0] : itemKey.type
        ) ? '+' : '-';
};

oml.getFileTypeColor = function(data) {
    return data.extension == 'epub' ? [[0, 128, 0], [128, 255, 128]]
        : data.extension == 'pdf' ? (
            data.textsize ? [[192, 0, 0], [255, 192, 192]]
                : [[192, 96, 0], [255, 192, 128]]
        )
        : data.extension == 'txt' ? [[255, 255, 255], [0, 0, 0]]
        : [[64, 64, 64], [192, 192, 192]];
};

oml.getFilterSizes = function() {
    var ui = oml.user.ui;
    return Ox.splitInt(
        window.innerWidth - ui.showSidebar * ui.sidebarSize - 1,
        5
    );
};

oml.getListFoldersHeight = function() {
    var ui = oml.user.ui;
    return Object.keys(ui.showFolder).reduce(function(value, id, index) {
        var items = oml.$ui.folderList[index].options('items').length;
        Ox.print('REDUCE', value, id, index, '...', items)
        return value + 16 + ui.showFolder[id] * (1 + items) * 16;
    }, 16);
};

oml.getListFoldersWidth = function() {
    var ui = oml.user.ui;
    Ox.print('HEIGHT::::', oml.getListFoldersHeight(), 'SCROLLBAR????', oml.$ui.appPanel
        && oml.getListFoldersHeight()
        > window.innerHeight - 20 - 24 - 1 - ui.showInfo * ui.sidebarSize)
    return ui.sidebarSize - (
        oml.$ui.appPanel
            && oml.getListFoldersHeight()
            > window.innerHeight - 20 - 24 - 1 - ui.showInfo * ui.sidebarSize
        ? Ox.UI.SCROLLBAR_SIZE : 0
    );
};

oml.hasDialogOrScreen = function() {
    return !!$('.OxDialog:visible').length
        || !!$('.OxFullscreen').length
        || !!$('.OxScreen').length;
};

oml.resizeFilters = function() {
    // ...
};

oml.resizeListFolders = function() {
    // FIXME: does this have to be here?
    Ox.print('RESIZING LIST FOLDERS', 'WIDTH', oml.getListFoldersWidth(), 'HEIGHT', oml.getListFoldersHeight())
    var width = oml.getListFoldersWidth(),
        columnWidth = width - 58;
    oml.$ui.librariesList
        .resizeColumn('title', columnWidth)
        .css({width: width + 'px'});
    Ox.forEach(oml.$ui.folder, function($folder, index) {
        $folder.css({width: width + 'px'});
        oml.$ui.libraryList[index]
            .resizeColumn('title', columnWidth)
            .css({width: width + 'px'});
        oml.$ui.folderList[index]
            .resizeColumn('title', columnWidth)
            .css({width: width + 'px'});
    });
    oml.$ui.librariesList
        .$body.find('.OxContent')
        .css({width: width + 'px'});
    Ox.forEach(oml.$ui.folder, function($folder, index) {    
        oml.$ui.libraryList[index]
            .$body.find('.OxContent')
            .css({width: width + 'px'});
        oml.$ui.folderList[index]
            .$body.find('.OxContent')
            .css({width: width + 'px'});
    })
};

oml.updateFilterMenus = function() {
    // FIXME: does this have to be a utils function?
    var selected = oml.$ui.filters.map(function($filter) {
            return !Ox.isEmpty($filter.options('selected'));
        }),
        filtersHaveSelection = !!Ox.sum(selected);
    oml.$ui.filters.forEach(function($filter, index) {
        $filter[
             selected[index] ? 'enableMenuItem' : 'disableMenuItem'
        ]('clearFilter');
        $filter[
            filtersHaveSelection ? 'enableMenuItem' : 'disableMenuItem'
        ]('clearFilters');
    });
};

oml.updateLists = function(callback) {
    // FIXME: can this go somewhere else?
    Ox.Request.clearCache('getLists');
    oml.api.getLists(function(result) {
        var items = result.data.lists[oml.user.id];
        oml.$ui.folderList[0].options({
                items: items
            })
            .css({height: items.length * 16 + 'px'})
            .size();
        oml.$ui.folder[0].$content
            .css({height: 16 + items.length * 16 + 'px'});
        callback && callback();
    });
};

oml.validateName = function(value, names) {
    var index = 1, length = 256, suffix;
    value = Ox.clean(Ox.clean(value).slice(0, length));
    names = names || [];
    while (Ox.contains(names, value)) {
        suffix = ' [' + (++index) + ']';
        value = value.replace(/ \[\d+\]$/, '')
            .slice(0, length - suffix.length) + suffix;
    };
    return value;
};

oml.validatePublicKey = function(value) {
    return /^[A-Za-z0-9+\/]{43}$/.test(value);
};

