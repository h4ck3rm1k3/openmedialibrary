'use strict';

oml.ui.itemToolbar = function() {

    var ui = oml.user.ui,

        that = Ox.Bar({size: 24})
            .css({zIndex: 2})
            .append(
                oml.$ui.backButton = oml.ui.backButton()
            ).append(
                oml.$ui.fullscreenButton = oml.ui.fullscreenButton()
            ).append(
                oml.$ui.itemViewButtons = oml.ui.itemViewButtons()
            );

    return that;

};
