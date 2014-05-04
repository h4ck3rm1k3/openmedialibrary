'use strict';

oml.ui.previewButton = function() {

    var ui = oml.user.ui,

        that = Ox.Button({
            selectable: true,
            style: 'squared',
            title: 'view',
            tooltip: Ox._('Preview {0}', [Ox.UI.symbols.space]),
            type: 'image'
        })
        .css({
            float: 'left',
            margin: '4px 2px'
        })
        .bindEvent({
            change: function(data) {
                oml.$ui.list[data.value ? 'openPreview' : 'closePreview']();
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