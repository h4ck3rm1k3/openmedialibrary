'use strict';

oml.ui.openButton = function() {

    var ui = oml.user.ui,

        that = Ox.Button({
            style: 'squared',
            title: 'arrowRight',
            tooltip: Ox._('Open Book {0}', [Ox.UI.symbols.return]),
            type: 'image'
        })
        .css({
            float: 'left',
            margin: '4px 2px 4px 4px'
        })
        .bindEvent({
            click: function() {
                oml.UI.set({item: ui.listSelection[0]});
            },
            oml_listselection: function() {
                that.update();
            }
        });

    that.update = function() {
        return that.options({disabled: ui.listSelection.length == 0});
    };

    return that.update();

};