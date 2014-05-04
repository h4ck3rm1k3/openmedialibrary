'use strict';

oml.ui.sortElement = function() {

    var ui = oml.user.ui,

        $sortSelect = Ox.Select({
            items: oml.config.sortKeys.map(function(key) {
                return Ox.extend({}, key, {
                    title: Ox._('Sort by {0}', [Ox._(key.title)])
                });
            }),
            style: 'squared',
            value: ui.listSort[0].key,
            width: 160
        })
        .bindEvent({
            change: function(data) {
                var key = data.value;
                oml.UI.set({
                    listSort: [{
                        key: key,
                        operator: oml.getSortOperator(key)
                    }]
                });
            }
        }),

        $orderButton = Ox.Button({
            overlap: 'left',
            style: 'squared',
            title: getButtonTitle(),
            tooltip: getButtonTooltip(),
            type: 'image'
        })
        .bindEvent({
            click: function() {
                oml.UI.set({
                    listSort: [{
                        key: ui.listSort[0].key,
                        operator: ui.listSort[0].operator == '+' ? '-' : '+'
                    }]
                });
            }
        }),

        that = Ox.FormElementGroup({
            elements: [$sortSelect, $orderButton],
            float: 'right'
        })
        .css({
            float: 'left',
            margin: '4px 2px'
        })
        .bindEvent({
            oml_listsort: function() {
                that.update();
            }
        });

    function getButtonTitle() {
        return ui.listSort[0].operator == '+' ? 'up' : 'down';
    }

    function getButtonTooltip() {
        return Ox._(ui.listSort[0].operator == '+' ? 'Ascending' : 'Descending');
    }

    that.update = function() {
        $sortSelect.value(ui.listSort[0].key);
        $orderButton.options({
            title: getButtonTitle(),
            tooltip: getButtonTooltip()
        });
        return that;
    };

    return that.update();

};