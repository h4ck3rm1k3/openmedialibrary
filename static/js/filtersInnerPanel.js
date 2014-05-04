'use strict';

oml.ui.filtersInnerPanel = function() {

    var filterSizes = oml.getFilterSizes(),

        that = Ox.SplitPanel({
            elements: [
                {
                    element: oml.$ui.filters[1],
                    size: filterSizes[1]
                },
                {
                    element: oml.$ui.filters[2]
                },
                {
                    element: oml.$ui.filters[3],
                    size: filterSizes[3]
                }
            ],
            orientation: 'horizontal'
        });

    return that;

};