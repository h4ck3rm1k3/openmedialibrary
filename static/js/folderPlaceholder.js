'use strict';

// FIXME: UNUSED

oml.ui.folderPlaceholder = function(text) {

    var that = Ox.Element()
            .addClass('OxLight')
            .css({
                height: '14px',
                padding: '1px 4px',
            });

    that.updateElement = function(text) {
        return that.html(text);
    };

    return that.updateElement(text);

};