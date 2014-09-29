'use strict';

oml.URL = (function() {

    var self = {}, that = {};

    function getHash(state, callback) {
        callback();
    }

    function getItem(state, string, callback) {
        oml.api.get({id: string, keys: ['id']}, function(result) {
            if (result.status.code == 200) {
                state.item = result.data.id;
            }
            callback();
        });
    }

    function getPart(state, string, callback) {
        var parts = Ox.getObjectById(oml.config.pages, state.page).parts || [];
        if (Ox.contains(parts, string)) {
            state.part = string;
        }
        callback();
    }

    function getSort(state, value, callback) {
        callback();
    }

    function getSpan(state, value, callback) {
        callback();
    }

    // translates UI settings to URL state
    function getState() {

        var state = {},
            ui = oml.user.ui;

        if (ui.page) {
            state.page = ui.page;
            if (Ox.contains(Object.keys(oml.config.user.ui.part), state.page)) {
                state.part = ui.part[state.page];                
            }
        } else {

            state.type = ui.section;
            state.item = ui.item;

            if (ui.section == 'books') {
                if (!ui.item) {
                    state.view = ui.listView;
                    state.sort = [ui.listSort[0]];
                    state.find = ui.find;
                } else {
                    state.view = ui.itemView;
                    if (ui.itemView == 'book') {
                        state.span = ui.mediaState[state.item] || [0, 1];
                    }
                }
            }

        }

        return state;

    }

    function getURLOptions() {

        var sortKeys = {},
            ui = oml.user.ui,
            views = {};

        views['books'] = {
            // ui.listView is the default view
            list: [ui.listView].concat(
                oml.config.listViews.filter(function(view) {
                    return view.id != ui.listView;
                }).map(function(view) {
                    return view.id;
                })
            ),
            // ui.itemView is the default view,
            item: [ui.itemView].concat(
                oml.config.itemViews.filter(function(view) {
                    return view.id != ui.itemView;
                }).map(function(view) {
                    return view.id;
                })
            )
        };

        sortKeys['books'] = {list: {}, item: {}};
        views['books'].list.forEach(function(view) {
            sortKeys['books'].list[view] = [].concat(
                // ui.listSort[0].key is the default sort key
                Ox.getObjectById(oml.config.sortKeys, ui.listSort[0].key),
                oml.config.sortKeys.filter(function(key) {
                    return key.id != ui.listSort[0].key;
                })
            );
        });

        return {
            findKeys: [{id: 'list', type: 'string'}].concat(
                oml.config.itemKeys
            ),
            pages: oml.config.pages.map(function(page) {
                return page.id;
            }),
            spanType: {
                books: {
                    list: {},
                    item: {
                        book: 'FIXME, no idea'
                    }
                }
            },
            sortKeys: sortKeys,
            types: ['books'],
            views: views
        };

    }

    // translates URL state to UI settings
    function setState(state, callback) {

        var set = {},
            ui = oml.user.ui;

        ui._list = oml.getListState(ui.find);
        ui._filterState = oml.getFilterState(ui.find);
        ui._findState = oml.getFindState(ui.find);

        if (Ox.isEmpty(state)) {

            callback && callback();

        } else {

            if (state.page) {

                set.page = state.page;
                if (
                    Ox.contains(Object.keys(oml.config.user.ui.part), state.page)
                    && state.part
                ) {
                    set['part.' + state.page] = state.part;
                }
                oml.UI.set(set);
                callback && callback();

            } else {

                set.page = '';

                if (state.type) {
                    set.section = state.type;
                    set.item = state.item;
                }

                if (set.section == 'books') {

                    if (state.view) {
                        set[!state.item ? 'listView' : 'itemView'] = state.view;
                    }

                    if (state.sort) {
                        set[!state.item ? 'listSort' : 'itemSort'] = state.sort;
                    }

                    if (state.span) {
                        if (state.view == 'book') {
                            set['mediaState.' + state.item] = {
                                position: state.span[0],
                                zoom: state.span[1]
                            };
                        }
                    }

                    if (!state.item) {
                        if (state.find) {
                            set.find = state.find;
                        } else if (!oml.$ui.appPanel) {
                            // when loading results without find, clear find, so that
                            // removing a query and reloading works as expected
                            set.find = oml.config.user.ui.find;
                        }
                    }

                }

                Ox.Request.cancel();

                 if (!oml.$ui.appPanel && state.item && ui.find) {
                    // on page load, if item is set and there was a query,
                    // we have to check if the item actually matches the query,
                    // and otherwise reset find
                    oml.api.find({
                        query: ui.find,
                        positions: [state.item],
                        sort: [{key: 'id', operator: ''}]
                    }, function(result) {
                        if (Ox.isUndefined(result.data.positions[state.item])) {
                            set.find = oml.config.user.ui.find
                        }
                        oml.UI.set(set);
                        callback && callback();
                    });
                } else {
                    oml.UI.set(set);
                    callback && callback();
                }

            }

        }

    }

    that.init = function() {

        self.URL = Ox.URL(Ox.extend({
            getHash: getHash,
            getItem: getItem,
            getPart: getPart,
            getSort: getSort,
            getSpan: getSpan,
        }, getURLOptions()));

        window.addEventListener('hashchange', function() {
            Ox.Request.cancel();
            that.parse();
        });

        window.addEventListener('popstate', function(e) {
            Ox.Request.cancel();
            self.isPopState = true;
            $('.OxDialog:visible').each(function() {
                Ox.$elements[$(this).data('oxid')].close();
            });
            if (e.state && !Ox.isEmpty(e.state)) {
                document.title = Ox.decodeHTMLEntities(e.state.title);
                setState(e.state);
            } else {
                that.parse();
            }

        });

        return that;

    };

    // on page load, this sets the state from the URL
    // can also be used to parse a URL
    that.parse = function(url, callback) {
        if (arguments.length == 2) {
            self.URL.parse(url, callback);
        } else {
            callback = arguments[0];
            url = null;
            if (document.location.pathname.slice(0, 4) == 'url=') {
                document.location.href = Ox.decodeURI(document.location.pathname.slice(4));
            } else {
                self.URL.parse(function(state) {
                    // setState -> UI.set -> URL.update
                    setState(state, callback);
                });
            }
        }
        return that;
    };

    // sets the URL to the previous URL
    that.pop = function() {
        self.URL.pop() || that.update();
        return that;
    };

    // pushes a new URL (as string or from state)
    that.push = function(stateOrURL, expandURL) {
        var state,
            title = oml.getPageTitle(stateOrURL),
            url;
        oml.replaceURL = expandURL;
        if (Ox.isObject(stateOrURL)) {
            state = stateOrURL;
        } else {
            url = stateOrURL;
        }
        self.URL.push(state, title, url, setState);
        return that;
    };

    // replaces the current URL (as string or from state)
    that.replace = function(stateOrURL, title) {
        var state,
            title = oml.getPageTitle(stateOrURL)
            url;
        if (Ox.isObject(stateOrURL)) {
            state = stateOrURL;
        } else {
            url = stateOrURL;
        }
        self.URL.push(state, title, url, setState);
        return that;
    };

    // this gets called from oml.UI
    that.update = function(keys) {
        var action, state;
        if (keys.some(function(key) {
            return Ox.contains(['itemView', 'listSort', 'listView'], key);
        })) {
            self.URL.options(getURLOptions());
        }
        if (self.isPopState) {
            self.isPopState = false;
        } else {
            if (
                !oml.$ui.appPanel
                || oml.replaceURL
                || keys.every(function(key) {
                    return Ox.contains([
                        'listColumnWidth', 'listColumns', 'listSelection'
                    ], key) || /^mediaState/.test(key);
                })
            ) {
                action = 'replace';
            } else {
                action = 'push';
            }
            state = getState();
            self.URL[action](
                state,
                oml.getPageTitle(state)
            );
            oml.replaceURL = false;
        }
    };

    return that;

}());
