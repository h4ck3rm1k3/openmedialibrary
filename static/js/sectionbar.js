'use strict';

oml.ui.sectionbar = function() {

    var ui = oml.user.ui,

        that = Ox.Bar({size: 24})
            .append(
                oml.$ui.sectionButtons = oml.ui.sectionButtons()
            );

    return that;

};