'use strict';

oml.ui.folders = function() {

    var ui = oml.user.ui,

        userIndex,
        users,

        $lists,

        that = Ox.Element()
            .css({
                overflowX: 'hidden',
            })
            .bindEvent({
                oml_find: selectList,
                oml_showfolder: function() {
                    oml.resizeListFolders();
                }
            });

    function getFind(list) {
        return {
            conditions: list ? [{
                key: 'list',
                operator: '==',
                value: list
            }] : [],
            operator: '&'
        };
    }

    function getFolderList(list) {
        var index = users.map(function(user) {
            return user.name;
        }).indexOf(list.user);
        return list.id == '' ? oml.$ui.librariesList
            : Ox.endsWith(list.id, ':') ? oml.$ui.libraryList[index]
            : oml.$ui.folderList[index];
    }

    function getUsersAndLists(callback) {
        oml.getUsers(function(users_) {
            users = users_.filter(function(user) {
                return user.id == oml.user.id || user.peered;
            });
            oml.getLists(function(lists) {
                callback(users, lists);
            });
        });
    }

    function selectList() {
        var split = ui._list.split(':'),
            index = userIndex[split[0]],
            list = split[1],
            $selectedList = !ui._list ? oml.$ui.librariesList
                : !list ? oml.$ui[!list ? 'libraryList' : 'folderList'][index]
                : oml.$ui.folderList[index];
        $lists.forEach(function($list) {
            if ($list == $selectedList) {
                $list.options({selected: [ui._list]}).gainFocus();
            } else {
                $list.options({selected: []})
            }
        });
    }

    that.updateElement = function() {

        that.empty();

        $lists = [];

        oml.$ui.folder = [];
        oml.$ui.libraryList = [];
        oml.$ui.folderList = [];

        getUsersAndLists(function(users, lists) {

            Ox.print('GOT USERS AND LISTS', users, lists);
            userIndex = {};

            $lists.push(
                oml.$ui.librariesList = oml.ui.folderList({
                        items: [lists[0]]
                    })
                    .bindEvent({
                        select: function() {
                            oml.UI.set({find: getFind('')});
                            oml.$ui.librariesList.options({selected: ['']});
                        },
                        selectnext: function() {
                            oml.UI.set(Ox.extend(
                                {find: getFind(':')},
                                'showFolder.',
                                true
                            ));
                        },
                    })
                    .css({height: '16px'})
                    .appendTo(that)
            );
            oml.$ui.librariesList.$body.css({height: '16px'}); // FIXME!

            users.forEach(function(user, index) {

                var $content,
                    items = lists.filter(function(list) {
                        return list.user === user.name
                            && list.type != 'library';
                    }),
                    libraryId = user.name + ':';

                userIndex[user.name] = index;

                oml.$ui.folder[index] = Ox.CollapsePanel({
                        collapsed: !ui.showFolder[user.name],
                        extras: [
                            oml.ui.statusIcon(user, index),
                            {},
                            Ox.Button({
                                style: 'symbol',
                                title: 'info',
                                tooltip: Ox._(!index ? 'Preferences...' : 'Profile...'),
                                type: 'image'
                            })
                            .bindEvent({
                                click: function() {
                                    if (!index) {
                                        oml.UI.set({
                                            page: 'preferences',
                                            'part.preferences': 'account'
                                        });
                                    } else {
                                        oml.UI.set({page: 'users'})
                                    }
                                }
                            })
                        ],
                        title: Ox.encodeHTMLEntities(
                            !index
                            ? oml.user.preferences.username || 'anonymous'
                            : user.name
                        )
                    })
                    .css({
                        width: ui.sidebarSize
                    })
                    .bindEvent({
                        toggle: function(data) {
                            oml.UI.set('showFolder.' + user.name, !data.collapsed);
                        }
                    })
                    .bindEvent(
                        'oml_showfolder.' + user.name.toLowerCase(),
                        function(data) {
                            oml.$ui.folder[index].options({collapsed: !data.value});
                        }
                    )
                    .appendTo(that);

                $content = oml.$ui.folder[index].$content
                    .css({
                        height: (1 + items.length) * 16 + 'px'
                    });

                $lists.push(
                    oml.$ui.libraryList[index] = oml.ui.folderList({
                            items: lists.filter(function(list) {
                                return list.user == user.name
                                    && list.type == 'library';
                            })
                        })
                        .bindEvent({
                            add: function() {
                                !index && oml.addList();
                            },
                            select: function(data) {
                                oml.UI.set({find: getFind(data.ids[0])});
                            },
                            selectnext: function() {
                                oml.UI.set({find: getFind(items[0].id)});
                            },
                            selectprevious: function() {
                                // FIXME: ugly
                                var set, user, userLists;
                                if (!index) {
                                    set = {find: getFind('')};
                                } else {
                                    user = users[index - 1].name;
                                    userLists = lists.filter(function(list) {
                                        return list.user == user;
                                    });
                                    set = {find: getFind(
                                        !userLists.length ? user + ':'
                                        : Ox.last(userLists).id
                                    )};
                                    Ox.extend(set, 'showFolder.' + user, true);
                                }
                                oml.UI.set(set);
                            }
                        })
                        .appendTo($content)
                );

                $lists.push(
                    oml.$ui.folderList[index] = oml.ui.folderList({
                            draggable: !!index,
                            items: items,
                            sortable: !index
                        })
                        .bindEvent({
                            add: function() {
                                !index && oml.addList();
                            },
                            'delete': function() {
                                !index && oml.ui.deleteListDialog().open();
                            },
                            key_control_d: function() {
                                oml.addList(ui._list);
                            },
                            move: function(data) {
                                lists[user.id] = data.ids.map(function(listId) {
                                    return Ox.getObjectById(items, listId);
                                });
                                oml.api.sortLists({
                                    ids: data.ids,
                                    user: user.id
                                }, function(result) {
                                    // ...
                                });
                            },
                            open: function() {
                                !index && oml.ui.listDialog().open();
                            },
                            select: function(data) {
                                oml.UI.set({find: getFind(data.ids[0])});
                            },
                            selectnext: function() {
                                if (index < users.length - 1) {
                                    oml.UI.set(Ox.extend(
                                        {find: getFind(users[index + 1].name + ':')},
                                        'showFolder.' + users[index + 1].name,
                                        true
                                    ));
                                }
                            },
                            selectprevious: function() {
                                oml.UI.set({find: getFind(libraryId)});
                            }
                        })
                        .css({height: items.length * 16 + 'px'})
                        .appendTo($content)
                );

                oml.$ui.folderList[index].$body.css({top: '16px'});

            });

            oml.resizeListFolders(); // FIXME: DOESN'T WORK
            selectList();

        });

        return that;

    };

    that.updateItems = function(items) {
        var $list;
        if (arguments.length == 0) {
            oml.getLists(function(lists) {
                lists.forEach(function(list) {
                    $list = getFolderList(list);
                    if ($list) {
                        $list.value(list.id, 'items', list.items);
                    }
                });
            });
        } else {
            $list = $lists.filter(function($list) {
                return $list.options('selected').length;
            })[0];
            if ($list && !Ox.isEmpty($list.value(ui._list))) {
                $list.value(ui._list, 'items', items);
            }
        }
    };

    that.updateOwnLists = function(callback) {
        oml.getLists(function(lists) {
            var items = lists.filter(function(list) {
                return list.user == '' && list.type != 'library';
            });
            oml.$ui.folder[0].$content
                .css({height: 16 + items.length * 16 + 'px'});
            oml.$ui.folderList[0].options({
                    items: items
                })
                .css({height: items.length * 16 + 'px'})
                .size();
            oml.resizeListFolders();
            callback && callback();
        });
    };

    oml.bindEvent({
        activity: function(data) {
            if (data.activity == 'import') {
                that.updateItems();
            }
        },
        change: function(data) {
            Ox.print('got change event')
        },
        'peering.accept': function(data) {
            Ox.print('peering.accept reload list')
            Ox.Request.clearCache('getUsers');
            that.updateElement();
        },
        'peering.remove': function(data) {
            Ox.print('peering.remove reload list')
            Ox.Request.clearCache('getUsers');
            that.updateElement();
        }
    });

    return that.updateElement();

};
