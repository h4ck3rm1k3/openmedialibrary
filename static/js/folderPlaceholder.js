'use strict';

// FIXME: UNUSED

oml.ui.folderPlaceholder = function(text) {

    var that = Ox.Element()
            .addClass('OxLight')
            .css({
                height: '14px',
                padding: '1px 4px',
            });

    that.updateText = function(text) {
        return that.html(text);
    };

    return that.updateText(text);

};