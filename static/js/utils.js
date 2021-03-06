oml.addList = function() {
    // addList(isSmart, isFrom[, name[, callback]])
    // or addList(list) [=duplicate]
    var args = arguments,
        isDuplicate = args.length == 1,
        isSmart, isFrom, name, callback,
        list, listData, data,
        ui = oml.user.ui,
        username = oml.user.preferences.username;
    Ox.Request.clearCache('getLists');
    oml.api.getLists(function(result) {
        var lists = result.data.lists,
            listNames = lists.filter(function(list) {
                return list.user = username;
            }).map(function(list) {
                return list.name;
            }),
            query;
        if (!isDuplicate) {
            isSmart = args[0];
            isFrom = args[1];
            name = args[2] || Ox._('Untitled');
            callback = args[3];
            data = {
                name: oml.getValidName(name, listNames),
                type: !isSmart ? 'static' : 'smart'
            };
            if (!isSmart) {
                if (isFrom) {
                    data.items = ui.listSelection;
                }
            } else {
                if (!isFrom) {
                    data.query = oml.config.user.ui.find;
                } else {
                    data.query = ui.find;
                }
            }
            addList();
        } else {
            list = args[0];
            listData = Ox.getObjectById(Ox.flatten(Ox.values(lists)), list);
            data = Ox.extend({
                name: oml.getValidName(listData.name, listNames),
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
        oml.api.addList(data, function(result) {
            var list = result.data.id,
                $folderList = oml.$ui.folderList[0];
            oml.$ui.folder[0].options({collapsed: false}); // FIXME: SET UI!
            // FIXME: DOESN'T WORK
            if (
                !oml.$ui.importExportDialog
                || !oml.$ui.importExportDialog.is(':visible')
            ) {
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
            }
            oml.$ui.folders.updateOwnLists();
            callback && callback();
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

oml.clickLink = function(e) {
    if (
        e.target.hostname == document.location.hostname
        && !Ox.startsWith(e.target.pathname, '/static')
    ) {
        oml.URL.push(e.target.pathname, true);
    } else {
        oml.openLink(e.target.href);
    }
};

oml.createLinks = function($element) {
    function isExternalLink(target) {
        return target.hostname != document.location.hostname
            || Ox.startsWith(target.pathname, '/static');
    } 
    $element.on({
        click: function(e) {
            var $target = $(e.target);
            if ($target.is('a')) {
                e.preventDefault();
                if (isExternalLink(e.target)) {
                    oml.openLink(e.target.href);
                } else {
                    oml.clickLink(e);
                }
            }
            return false;
        }
    });
};

(function() {

    oml.doHistory = function(action, items, targets, callback) {
        items = Ox.makeArray(items);
        targets = Ox.makeArray(targets);
        if (action == 'copy' || action == 'paste') {
            addItems(items, targets[0], addToHistory);
        } else if (action == 'cut' || action == 'delete') {
            removeItems(items, targets[0], addToHistory);
        } else if (action == 'move') {
            removeItems(items, targets[0], function() {
                addItems(items, targets[1], addToHistory);
            });
        }
        function addToHistory(result, addedItems) {
            var actions = {
                    copy: 'Copying',
                    cut: 'Cutting',
                    'delete': 'Deleting',
                    move: 'Moving',
                    paste: 'Pasting'
                },
                length = items.length,
                text = Ox._(actions[action]) + ' ' + (
                    length == 1 ? 'Book' : 'Books'
                );
            oml.history.add({
                action: action,
                items: action == 'cut' || action == 'delete' ? [items]
                    : action == 'copy' || action == 'paste' ? [addedItems]
                    : [items, addedItems], // move
                positions: [],
                targets: targets,
                text: text
            });
            callback(result);
        }
    };

    oml.redoHistory = function(callback) {
        var object = oml.history.redo();
        if (object) {
            if (object.action == 'copy' || object.action == 'paste') {
                addItems(object.items[0], object.targets[0], done);
            } else if (object.action == 'cut' || object.action == 'delete') {
                removeItems(object.items[0], object.targets[0], done);
            } else if (object.action == 'move') {
                removeItems(object.items[0], object.targets[0], function() {
                    addItems(object.items[1], object.targets[1], done);
                });
            }
        }
        function done() {
            doneHistory(object, callback);
        }
    };

    oml.undoHistory = function(callback) {
        var object = oml.history.undo();
        if (object) {
            if (object.action == 'copy' || object.action == 'paste') {
                removeItems(object.items[0], object.targets[0], done);
            } else if (object.action == 'cut' || object.action == 'delete') {
                addItems(object.items[0], object.targets[0], done);
            } else if (object.action == 'move') {
                removeItems(object.items[1], object.targets[1], function() {
                    addItems(object.items[0], object.targets[0], done);
                });
            }
        }
        function done() {
            doneHistory(object, callback);
        }
    };

    function addItems(items, target, callback) {
        oml.api.find({
            query: {
                conditions: [{
                    key: 'list',
                    operator: '==',
                    value: target
                }],
                operator: '&'
            },
            positions: items
        }, function(result) {
            var existingItems = Object.keys(result.data.positions),
                addedItems = items.filter(function(item) {
                    return !Ox.contains(existingItems, item);
                });
            if (addedItems.length) {
                oml.api.addListItems({
                    items: addedItems,
                    list: target
                }, function(result) {
                    Ox.Request.clearCache();
                    callback(result, addedItems);
                });                    
            } else {
                callback(null, []);
            }
        });
    }

    function doneHistory(object, callback) {
        var list, listData, ui = oml.user.ui;
        Ox.Request.clearCache('find');
        object.targets.filter(function(list) {
            return list != ui._list;
        }).forEach(function(list) {
            listData = oml.getListData(list);
            oml.api.find({
                query: {
                    conditions: [{
                        key: 'list',
                        operator: '==',
                        value: list
                    }],
                    operator: '&'
                }
            }, function(result) {
                oml.$ui.folderList[listData.folder].value(
                    list, 'items', result.data.items
                );
            });
        });
        if (Ox.contains(object.targets, ui._list)) {
            // FIXME: Why is this timeout needed?
            setTimeout(oml.reloadList, 250);
        }
        callback && callback();
    }

    function removeItems(items, target, callback) {
        oml.api.removeListItems({
            items: items,
            list: target
        }, callback);
    }

}());

oml.enableDragAndDrop = function($list, canMove) {

    var $tooltip = Ox.Tooltip({
            animate: false
        }),
        drag = {},
        scrollInterval,
        ui = oml.user.ui;

    $list.bindEvent({
        draganddropstart: function(data) {
            var $lists = oml.$ui.libraryList.concat(oml.$ui.folderList);
            drag.action = 'copy';
            drag.ids = $list.options('selected');
            drag.item = drag.ids.length == 1
                ? Ox.decodeHTMLEntities($list.value(drag.ids[0], 'title'))
                : drag.ids.length;
            drag.source = oml.getListData();
            drag.targets = {};
            $lists.forEach(function($list) {
                $list.addClass('OxDroppable').find('.OxItem').each(function() {
                    var $item = $(this),
                        id = $item.data('id'),
                        data = oml.getListData(id);
                    drag.targets[id] = Ox.extend(data, {
                        editable: data.editable || (
                            data.type == 'library'
                            && drag.source.user != ''
                            && data.user == ''
                        ),
                        selected: data.id == ui._list
                    }, data);
                    if (!drag.targets[id].selected && drag.targets[id].editable) {
                        $item.addClass('OxDroppable');
                    }
                });
            });
            $tooltip.options({title: getTitle()}).show(data.event);
            Ox.$window.on({
                keydown: keydown,
                keyup: keyup
            });
        },
        draganddrop: function(data) {
            var event = data.event;
            $tooltip.options({
                title: getTitle(event)
            }).show(event);
            if (scrollInterval && !isAtListsTop(event) && !isAtListsBottom(event)) {
                clearInterval(scrollInterval);
                scrollInterval = 0;
            }
        },
        draganddroppause: function(data) {
            var event = data.event, scroll, title,
                ui = oml.user.ui,
                $parent, $grandparent, $panel;
            if (!ui.showSidebar) {
                if (event.clientX < 16 && event.clientY >= 44
                    && event.clientY < window.innerHeight - 16
                ) {
                    oml.$ui.mainPanel.toggleElement(0);
                }
            } else {
                $parent = $(event.target).parent();
                $grandparent = $parent.parent();
                $panel = $parent.is('.OxCollapsePanel') ? $parent
                    : $grandparent.is('.OxCollapsePanel') ? $grandparent
                    : null;
                if ($panel) {
                    title = $panel.children('.OxBar').children('.OxTitle')
                        .html().split(' ')[0].toLowerCase();
                    if (!ui.showFolder[title]) {
                        Ox.$elements[$panel.data('oxid')].options({
                            collapsed: false
                        });
                    }
                }
                if (!scrollInterval) {
                    scroll = isAtListsTop(event) ? -16
                        : isAtListsBottom(event) ? 16
                        : 0
                    if (scroll) {
                        scrollInterval = setInterval(function() {
                            oml.$ui.folders.scrollTop(
                                oml.$ui.folders.scrollTop() + scroll
                            );
                        }, 100);
                    }
                }
            }
        },
        draganddropenter: function(data) {
            var $parent = $(data.event.target).parent(),
                $item = $parent.is('.OxItem') ? $parent : $parent.parent(),
                $list = $item.parent().parent().parent().parent();
            if ($list.is('.OxDroppable')) {
                $item.addClass('OxDrop');
                drag.target = drag.targets[$item.data('id')];
            } else {
                drag.target = null;
            }
        },
        draganddropleave: function(data) {
            var $parent = $(data.event.target).parent(),
                $item = $parent.is('.OxItem') ? $parent : $parent.parent();
            if ($item.is('.OxDroppable')) {
                $item.removeClass('OxDrop');
                drag.target = null;
            }
        },
        draganddropend: function(data) {
            var targets;
            Ox.$window.off({
                keydown: keydown,
                keyup: keyup
            });
            if (
                drag.target && drag.target.editable && !drag.target.selected
                && (drag.action == 'copy' || drag.source.editable)
            ) {
                var targets = drag.action == 'copy' ? drag.target.id
                    : [oml.user.ui._list, drag.target.id];
                oml.doHistory(drag.action, data.ids, targets, function() {
                    Ox.Request.clearCache('find');
                    oml.api.find({
                        query: {
                            conditions: [{
                                key: 'list',
                                operator: '==',
                                value: drag.target.id
                            }],
                            operator: '&'
                        }
                    }, function(result) {
                        /* FIXME
                        oml.$ui.folderList[drag.target.folder].value(
                            drag.target.id, 'items', result.data.items
                        );
                        */
                        cleanup(250);
                    });
                    oml.$ui.folders.updateItems();
                    if (drag.action == 'move') {
                        oml.$ui.list.updateElement();
                    }
                });
            } else {
                cleanup()
            }
        }
    });

    function cleanup(ms) {
        ms = ms || 0;
        drag = {};
        clearInterval(scrollInterval);
        scrollInterval = 0;
        setTimeout(function() {
            $('.OxDroppable').removeClass('OxDroppable');
            $('.OxDrop').removeClass('OxDrop');
            $tooltip.hide();
        }, ms);
    }

    function getTitle() {
        var image, text,
            actionText = drag.action == 'copy' ? (
                drag.source.user == '' ? 'copy' : 'download'
            ) : 'move',
            itemText = Ox.isString(drag.item)
                ? '"' + Ox.encodeHTMLEntities(Ox.truncate(drag.item, 32)) + '"'
                : Ox._('{0} books', [drag.item]),
            targetText;
        if (drag.action == 'move') {
            if (drag.source.user != '') {
                text = Ox._('You can only remove books<br>from your own lists.');
            } else if (drag.source.type == 'library') {
                text = Ox._('You cannot move books<br>out of your library.');
            } else if (drag.source.type == 'smart') {
                text = Ox._('You cannot move books<br>out of a smart list.');
            }
        } else if (drag.target) {
            targetText = drag.target.type == 'libraries' ? Ox._('a library')
                : drag.target.type == 'library' ? Ox._('your library')
                : Ox._('the list "{0}"', [Ox.encodeHTMLEntities(Ox.truncate(drag.target.name, 32))]);
            if (
                (
                    drag.target.type == 'library'
                    && drag.source.user == ''
                    && drag.target.user == ''
                )
                || drag.target.selected
            ) {
                text = Ox._('{0}<br>is already in {1}.', [
                    Ox._(itemText[0] == '"' ? '' : 'These ') + itemText,
                    targetText
                ]);
            } else if (drag.target.user != '') {
                text = Ox._(
                    'You can only {0} books<br>to your own {1}.',
                    [actionText, drag.target.type == 'library' ? 'library' : 'lists']
                );
            } else if (drag.target.type == 'smart') {
                text = Ox._('You cannot {0} books<br>to a smart list.', [actionText]);
            }
        }
        if (text) {
            image = 'symbolClose'
        } else {
            image = drag.action == 'copy' ? (
                drag.source.user == '' ? 'symbolAdd' : 'symbolDownload'
            ) : 'symbolRemove',
            text = Ox._(Ox.toTitleCase(actionText)) + ' ' + (
                Ox.isString(drag.item)
                ? '"' + Ox.encodeHTMLEntities(Ox.truncate(drag.item, 32)) + '"'
                : drag.item + ' ' + 'books'
            ) + '<br>' + (
                drag.target && drag.target.editable && !drag.target.selected
                ? Ox._('to {0}.', [targetText])
                : drag.source.user == '' 
                ? Ox._('to {0} list.', [ui._list == ':' ? 'a' : 'another'])
                : Ox._('to your library or to one of your lists.')
            );
        }
        return $('<div>')
            .append(
                $('<div>')
                    .css({
                        float: 'left',
                        width: '16px',
                        height: '16px',
                        padding: '1px',
                        border: '3px solid rgb(' + Ox.Theme.getThemeData().symbolDefaultColor.join(', ') + ')',
                        borderRadius: '12px',
                        margin: '3px 2px 2px 2px'
                    })
                    .append(
                         $('<img>')
                            .attr({src: Ox.UI.getImageURL(image)})
                            .css({width: '16px', height: '16px'})
                    )
            )
            .append(
                $('<div>')
                    .css({
                        float: 'left',
                        margin: '1px 2px 2px 2px',
                        fontSize: '11px',
                        whiteSpace: 'nowrap'
                    })
                    .html(text)
            );
    }

    function isAtListsTop(e) {
        return ui.showSidebar
            && e.clientX < ui.sidebarSize
            && e.clientY >= 44 && e.clientY < 60;
    }

    function isAtListsBottom(e) {
        var listsBottom = window.innerHeight - oml.getInfoHeight();
        return ui.showSidebar
            && e.clientX < ui.sidebarSize
            && e.clientY >= listsBottom - 16 && e.clientY < listsBottom;
    }

    function keydown(e) {
        if (e.metaKey) {
            drag.action = 'move';
            $tooltip.options({title: getTitle()}).show();
        }
    }

    function keyup(e) {
        if (drag.action == 'move') {
            drag.action = 'copy';
            $tooltip.options({title: getTitle()}).show();
        }
    }

};

oml.getEditTooltip = function(title) {
    return function(e) {
        var $target = $(e.target);
        return (
            $target.is('a') || $target.parents('a').length
            ? Ox._('Shift+doubleclick to edit') : Ox._('Doubleclick to edit')
        ) + (title ? ' ' + Ox._(title) : '');
    }
};

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

oml.getFilterSizes = function() {
    var ui = oml.user.ui;
    return Ox.splitInt(
        window.innerWidth - ui.showSidebar * ui.sidebarSize - 1,
        5
    );
};

oml.getIconInfoColor = function(type, data) {
    return type == 'extension' ? (
        data.extension == 'epub' ? [[32, 160, 32], [0, 128, 0], [128, 255, 128]]
        : data.extension == 'pdf' ? (
            data.textsize
            ? [[224, 32, 32], [192, 0, 0], [255, 192, 192]]
            : [[224, 128, 32], [192, 96, 0], [255, 192, 128]]
        )
        : data.extension == 'txt' ? [[255, 255, 255], [224, 224, 224], [0, 0, 0]]
        : [[96, 96, 96], [64, 64, 64], [192, 192, 192]]
    ) : data.mediastate == 'available' ? [[32, 160, 32], [0, 128, 0], [128, 255, 128]]
    : data.mediastate == 'transferring' ? [[160, 160, 32], [128, 128, 0], [255, 255, 128]]
    : [[224, 32, 32], [192, 0, 0], [255, 192, 192]];
};

oml.getInfoHeight = function() {
    return Math.min(
        oml.user.ui.sidebarSize,
        window.innerHeight - 20 - 24 - 16 - 1
    );
};

oml.getListData = function(list) {
    var ui = oml.user.ui;
    list = Ox.isUndefined(list) ? ui._list : list;
    return ui._lists ? Ox.getObjectById(ui._lists, list) : {};
};

oml.getListFoldersHeight = function() {
    var ui = oml.user.ui;
    return oml.$ui.folder.reduce(function(value, $folder, index) {
        var items = oml.$ui.folderList[index].options('items').length;
        return value + 16 + !$folder.options('collapsed') * (1 + items) * 16;
    }, 16);
};

oml.getListFoldersWidth = function() {
    var ui = oml.user.ui;
    return ui.sidebarSize - (
        oml.$ui.appPanel
            && oml.getListFoldersHeight()
            > window.innerHeight - 20 - 24 - 1 - ui.showInfo * oml.getInfoHeight()
        ? Ox.UI.SCROLLBAR_SIZE : 0
    );
};

oml.getLists = function(callback) {
    var ui = oml.user.ui;
    Ox.Request.clearCache('getLists');
    oml.api.getLists(function(result) {
        ui._lists = result.data.lists.map(function(list) {
            // FIXME: 'editable' is notoriously vague
            list.name = list.type == 'libraries' ? Ox._('Libraries')
                 : list.type == 'library' ? Ox._('Library') : list.name;
            return Ox.extend(list, {
                editable: list.user == '' && list.type == 'static',
                own: list.user == '',
                title: (list.user ? list.user + ': ' : '') + list.name
            });
        });
        callback(ui._lists);
    });
};

oml.getOwnListNames = function() {
    var ui = oml.user.ui;
    return ui._lists.filter(function(list) {
        return list.user == '' && list.type != 'library';
    }).map(function(list) {
        return list.name;
    });
};

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

oml.getUsers = function(callback) {
    var ui = oml.user.ui;
    Ox.Request.clearCache('getUsers');
    oml.api.getUsers(function(result) {
        var users = [{
            id: oml.user.id,
            name: '',
            online: oml.user.online
        }].concat(
            Ox.sortBy(result.data.users.filter(function(user) {
                return user.peered;
            }), 'index') 
        );
        ui._users = users;
        callback(users);
    });
};

oml.getValidName = function(value, names, chars) {
    var index = 1, length = 256, suffix;
    if (chars) {
        value = value.replace(
            new RegExp('[' + Ox.escapeRegExp(chars) + ']', 'g'),
            ''
        );
    }
    value = Ox.clean(Ox.clean(value).slice(0, length));
    names = names || [];
    while (Ox.contains(names, value)) {
        suffix = ' [' + (++index) + ']';
        value = value.replace(/ \[\d+\]$/, '')
            .slice(0, length - suffix.length) + suffix;
    };
    return value;
};

oml.hasDialogOrScreen = function() {
    return !!$('.OxDialog:visible').length
        || !!$('.OxFullscreen').length
        || !!$('.OxScreen').length;
};

oml.openLink = function(url) {
    if (Ox.startsWith(url, 'mailto:')) {
        window.open(url);
    } else {
        window.open('/url=' + encodeURIComponent(url), '_blank');
    }
};

oml.reloadList = function() {
    oml.$ui.list.updateElement();
};

oml.renameUser = function(data) {

    var ui = oml.user.ui,
        index = Ox.getIndexById(ui._users, data.id),
        name,
        set = {},
        oldFind,
        newFind;
    if (index == -1) {
        return;
    }

    name = ui._users[index].name;
    oldFind = Ox.clone(ui.find, true);
    newFind = Ox.clone(ui.find, true);
    ui._users[index].name = data.name;
    ui._users[index].nickname = data.nickname;
    set['showFolder.' + oml.UI.encode(name)] = null;
    set['showFolder.' + oml.UI.encode(data.name)] = ui.showFolder[name];
    Ox.forEach(ui.lists, function(value, key) {
        var split = key.split(':'),
            username = split[0],
            listname = split.slice(1).join(':');
        if (username == name) {
            set['lists.' + oml.UI.encode(key)] = null;
            set['lists.' + oml.UI.encode(data.name + ':' + listname)] = value;
        }
    });

    ui._lists.filter(function(list) {
        return list.user === '' && list.type == 'smart';
    }).forEach(function(list) {
        updateConditions(list.query);
    });
    oml.UI.set(set, false);

    updateConditions(newFind);
    if (!Ox.isEqual(oldFind, newFind)) {
        oml.replaceURL = true;
        oml.UI.set({find: newFind}, false);
    }
    oml.$ui.folders.updateUser(index);

    function updateCondition(condition) {
        if (condition.key == 'list') {
            condition.value = condition.value.replace(
                new RegExp('^' + Ox.escapeRegExp(name) + ':'),
                data.name + ':'
            );
        }
    }

    function updateConditions(query) {
        query.conditions.forEach(function(condition) {
            if (!condition.conditions) {
                updateCondition(condition);
            } else {
                condition.conditions.forEach(updateCondition);
            }
        });
    }
    
};

oml.resizeFilters = function() {
    // ...
};

oml.resizeListFolders = function() {
    // FIXME: does this have to be here?
    var width = oml.getListFoldersWidth(),
        columnWidth = width - 16 - 48;
    oml.$ui.librariesList
        .css({width: width + 'px'})
        .resizeColumn('name', columnWidth);
    Ox.forEach(oml.$ui.folder, function($folder, index) {
        $folder.css({width: width + 'px'});
        oml.$ui.libraryList[index]
            .css({width: width + 'px'})
            .resizeColumn('name', columnWidth);
        oml.$ui.folderList[index]
            .css({width: width + 'px'})
            .resizeColumn('name', columnWidth);
    });
};

oml.resizeWindow = function() {
    oml.$ui.leftPanel && oml.$ui.leftPanel.size(2, oml.getInfoHeight());
    oml.resizeListFolders();
    oml.$ui.rightPanel && oml.$ui.rightPanel.updateElement();
    oml.$ui.list && oml.$ui.list.size();
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

oml.validatePublicKey = function(value) {
    return /^[a-z0-9+\/]{16}$/.test(value);
};

oml.updateDebugMenu = function() {
    var menu = $('.OxTitle').filter(function(i, e) {
        return e.innerHTML == 'Debug'
    });
    oml.user.ui.showDebugMenu ? menu.show() : menu.hide();
};

oml.supportedExtensions = ['pdf', 'epub', 'cbr', 'cbz'];
oml.upload = function(files, callback) {
    var request = new XMLHttpRequest(),
        url = '/api/upload/';
    request.onreadystatechange = function() {
        if (request.readyState == 4) {
            if (request.status == 200) {
                callback(JSON.parse(request.responseText), null);
            } else {
                callback(null, {
                    code: request.status,
                    text: request.statusText
                });
            }
        }
    };
    var formData = new FormData();
    for (var i=0; i < files.length; i++) {
        var extension = Ox.last(files[i].name.split('.'));
        if (Ox.contains(oml.supportedExtensions, extension)) {
            formData.append('files', files[i]);
        }
    }
    if (oml.user.ui._list[0] == ':' && oml.user.ui._list.length > 1) {
        formData.append('list', oml.user.ui._list.slice(1));
    }
    request.open('post', url, true);
    request.send(formData);
};
