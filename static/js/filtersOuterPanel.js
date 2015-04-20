'use strict';

oml.ui.filtersOuterPanel = function() {

    var ui = oml.user.ui,

        $filters = oml.$ui.filters = ui.filters.map(function(filter) {
            return oml.ui.filter(filter.id);
        }),

        filterSizes = oml.getFilterSizes(),

        that = Ox.SplitPanel({
            elements: [
                {
                    element: $filters[0],
                    size: filterSizes[0]
                },
                {
                    element: oml.$ui.filtersInnerPanel = oml.ui.filtersInnerPanel()
                },
                {
                    element: $filters[4],
                    size: filterSizes[4]
                },
            ],
            orientation: 'horizontal'
        })
        .bindEvent({
            resize: function() {
                oml.$ui.filters.forEach(function($filter) {
                    $filter.size();
                });
            },
            resizeend: function(data) {
                oml.UI.set({filtersSize: data.size});
            },
            toggle: function(data) {
                if (data.collapsed) {
                    oml.$ui.list.gainFocus();
                }
                oml.UI.set({showFilters: !data.collapsed});
                if (!data.collapsed) {
                    oml.$ui.filters.forEach(function($filter) {
                        var selected = $filter.options('_selected');
                        if (selected) {
                            $filter.bindEventOnce({
                                load: function() {
                                    $filter.options({
                                        _selected: false,
                                        selected: selected
                                    });
                                }
                            }).reloadList();                            
                        }
                    });
                    oml.updateFilterMenus();
                }
            },
            oml_find: function() {
                var previousUI = oml.UI.getPrevious();
                ui._filterState.forEach(function(data, index) {
                    if (!Ox.isEqual(data.selected, previousUI._filterState[index].selected)) {
                        oml.$ui.filters[index].options(
                            ui.showFilters ? {
                                selected: data.selected
                            } : {
                                _selected: data.selected,
                                selected: []
                            }
                        );
                    }
                    if (!Ox.isEqual(data.find, previousUI._filterState[index].find)) {
                        if (!ui.showFilters) {
                            oml.$ui.filters[index].options({
                                _selected: data.selected
                            });
                        }
                        // we can call reloadList here, since the items function
                        // handles the hidden filters case without making requests
                        oml.$ui.filters[index].reloadList();
                    }
                });
            }
        });

    oml.updateFilterMenus();

    that.updateElement = function() {
        var filterSizes = oml.getFilterSizes();
        that.size(0, filterSizes[0])
            .size(2, filterSizes[4]);
        oml.$ui.filtersInnerPanel
            .size(0, filterSizes[1])
            .size(2, filterSizes[3]);
        oml.$ui.filters.forEach(function($filter, index) {
            $filter.resizeColumn(
                'name',
                filterSizes[index] - 48 - Ox.UI.SCROLLBAR_SIZE
            );
        });
        return that;
    };

    return that;

};
