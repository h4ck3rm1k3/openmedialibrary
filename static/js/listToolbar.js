'use strict';

oml.ui.listToolbar = function() {

    var ui = oml.user.ui,

        that = Ox.Bar({size: 24})
            .css({zIndex: 2})
            .append(
                oml.$ui.openButton = oml.ui.openButton()
            ).append(
                oml.$ui.previewButton = oml.ui.previewButton()
            ).append(
                oml.$ui.listViewButtons = oml.ui.listViewButtons()
            ).append(
                oml.$ui.sortElement = oml.ui.sortElement()
            ).append(
                oml.$ui.findElement = oml.ui.findElement()
            );

    return that;

};