'use strict';

oml.ui.iconDialog = function(options) {

    var options = Ox.extend({
            closeButton: false,
            content: '',
            height: 128,
            keys: null,
            title: '',
            width: 368,
        }, options),

        that = Ox.Dialog({
            buttons: options.buttons,
            closeButton: options.closeButton,
            content: Ox.Element()
                .append(
                    $('<img>')
                        .attr({src: '/static/png/oml.png'})
                        .css({position: 'absolute', left: '16px', top: '16px', width: '64px', height: '64px'})
                )
                .append(
                    Ox.isObject(options.content)
                    ? options.content
                        .css({position: 'absolute', left: '96px', top: '16px', width: options.width - 112 + 'px'})
                    : $('<div>')
                        .addClass('OxTextPage')
                        .css({position: 'absolute', left: '96px', top: '16px', width: options.width - 112 + 'px'})
                        .html(options.content)
                ),
            fixedSize: true,
            height: options.height,
            keys: options.keys,
            removeOnClose: true,
            title: options.title,
            width: options.width
        });

    return that;

};