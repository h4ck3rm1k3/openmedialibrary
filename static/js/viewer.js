'use strict';

oml.ui.viewer = function() {

    var ui = oml.user.ui,

        that = Ox.Element()
            .bindEvent({
                oml_item: function(data) {
                    that.update();
                },
                oml_itemview: function(data) {
                    that.update();
                }
            }),

        $iframe;

    that.update = function() {
        if (ui.item && ui.itemView == 'book') {
            $iframe = $iframe || Ox.Element('<iframe>').css({
                width: '100%',
                height: '100%',
                border: 0
            }).appendTo(that);
            $iframe.attr({
                src: '/' + ui.item + '/reader/'
            });
        }
        return that;
    };

    return that.update();

};
