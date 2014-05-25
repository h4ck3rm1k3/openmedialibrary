'use strict';

oml.ui.viewer = function() {

    var ui = oml.user.ui,

        that = Ox.Element()
            .bindEvent({
                oml_itemview: function(data) {
                    if (ui.item != item && ui.itemView == 'book') {
                        that.updateElement(ui.item);
                    }
                }
            }),

        $iframe, item;

    that.updateElement = function() {
        item = ui.item;
        if (item) {
            $iframe = $iframe || Ox.Element('<iframe>').css({
                width: '100%',
                height: '100%',
                border: 0
            }).appendTo(that);
            $iframe.attr({
                src: '/' + item + '/reader/'
            });
        }
        return that;
    };

    return that.updateElement();

};
