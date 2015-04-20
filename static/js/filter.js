'use strict';

oml.ui.filter = function(id) {

    var ui = oml.user.ui,
        filter = Ox.getObjectById(oml.config.filters, id),
        filterIndex = Ox.getIndexById(ui.filters, id),
        filterSize = oml.getFilterSizes()[filterIndex],

        that = Ox.TableList({
            _selected: !ui.showFilters
                ? ui._filterState[filterIndex].selected
                : false,
            columns: [
                {
                    id: 'name',
                    operator: '+',
                    title: Ox._(filter.title),
                    visible: true,
                    width: filterSize - 48 - Ox.UI.SCROLLBAR_SIZE
                },
                {
                    align: 'right',
                    format: function(value) {
                        return Ox.formatNumber(value);
                    },
                    id: 'items',
                    operator: '-',
                    title: '#',
                    visible: true,
                    width: 48
                }
            ],
            columnsVisible: true,
            items: function(data, callback) {
                if (ui.showFilters) {
                    delete data.keys;
                    return oml.api.find(Ox.extend(data, {
                        group: filter.id,
                        query: ui._filterState[filterIndex].find
                    }), callback);
                } else {
                    callback({
                        data: {items: data.keys ? [] : 0}
                    });
                }
            },
            scrollbarVisible: true,
            selected: ui.showFilters
                ? ui._filterState[filterIndex].selected
                : [],
            sort: Ox.clone(ui.filters[filterIndex].sort, true),
            unique: 'name'
        })
        .bindEvent({
            init: function(data) {
                that.setColumnTitle(
                    'name',
                    Ox._(filter.title)
                    + '<div class="OxColumnStatus OxLight">'
                    + Ox.formatNumber(data.items) + '</div>'
                );
            },
            select: function(data) {
                // fixme: cant index be an empty array, instead of -1?
                // FIXME: this is still incorrect when deselecting a filter item
                // makes a selected item in another filter disappear
                var conditions = data.ids.map(function(value) {
                        return {
                            key: id,
                            value: value,
                            operator: '=='
                        };
                    }),
                    index = ui._filterState[filterIndex].index,
                    find = Ox.clone(ui.find, true);
                if (Ox.isArray(index)) {
                    // this filter had multiple selections and the | query
                    // was on the top level, i.e. not bracketed
                    find = {
                        conditions: conditions,
                        operator: conditions.length > 1 ? '|' : '&'
                    }
                } else {
                    if (index == -1) {
                        // this filter had no selection, i.e. no query
                        index = find.conditions.length;
                        if (find.operator == '|') {
                            find = {
                                conditions: [find],
                                operator: '&'
                            };
                            index = 1;
                        } else {
                            find.operator = '&';
                        }
                    }
                    if (conditions.length == 0) {
                        // nothing selected
                        find.conditions.splice(index, 1);
                        if (find.conditions.length == 1) {
                            if (find.conditions[0].conditions) {
                                // unwrap single remaining bracketed query
                                find = {
                                    conditions: find.conditions[0].conditions,
                                    operator: '|'
                                };
                            } else {
                                find.operator = '&';
                            }
                        }
                    } else if (conditions.length == 1) {
                        // one item selected
                        find.conditions[index] = conditions[0];
                    } else {
                        // multiple items selected
                        if (ui.find.conditions.length == 1) {
                            find = {
                                conditions: conditions,
                                operator: '|'
                            };
                        } else {
                            find.conditions[index] = {
                                conditions: conditions,
                                operator: '|'
                            };
                        }
                    }
                }
                oml.UI.set({find: find});
                oml.updateFilterMenus();
            },
            sort: function(data) {
                var filters = Ox.clone(ui.filters, true);
                filters[filterIndex].sort = [{key: data.key, operator: data.operator}];
                oml.UI.set({filters: filters});
            }
        }),

        $menu = Ox.MenuButton({
            items: [
                {id: 'clearFilter', title: Ox._('Clear Filter'), keyboard: 'shift control a'},
                {id: 'clearFilters', title: Ox._('Clear All Filters'), keyboard: 'shift alt control a'},
                {},
                {group: 'filter', max: 1, min: 1, items: oml.config.filters.map(function(filter) {
                    return Ox.extend({checked: filter.id == id}, filter);
                })}
            ],
            type: 'image',
        })
        .css(Ox.UI.SCROLLBAR_SIZE == 16 ? {
            right: 0,
            width: '14px'
        } : {
            right: '-1px',
            width: '8px',
        })
        .bindEvent({
            change: function(data) {
                var isOuter = filterIndex % 4 == 0, id = data.checked[0].id;
                ui.filters[filterIndex] = Ox.getObjectById(oml.config.user.ui.filters, id);
                ui._filterState = oml.getFilterState(ui.find);
                oml.$ui[isOuter ? 'filtersOuterPanel' : 'filtersInnerPanel'].replaceElement(
                    isOuter ? filterIndex / 2 : filterIndex - 1,
                    oml.$ui.filters[filterIndex] = oml.ui.filter(id)
                );
            },
            click: function(data) {
                if (data.id == 'clearFilter') {
                    that.options({selected: []}).triggerEvent('select', {ids: []});
                } else if (data.id == 'clearFilters') {
                    oml.clearFilters();
                }
            }
        })
        .appendTo(that.$bar.$element);

    if (Ox.UI.SCROLLBAR_SIZE < 16) {
        $($menu.find('input')[0]).css({
            marginRight: '-3px',
            marginTop: '1px',
            width: '8px',
            height: '8px'
        });
    }

    that.disableMenuItem = function(id) {
        $menu.disableItem(id);
    };

    that.enableMenuItem = function(id) {
        $menu.enableItem(id);
    };

    return that;

};
