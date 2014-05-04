'use strict';

oml.ui.sectionButtons = function() {

    var ui = oml.user.ui,

        that = Ox.ButtonGroup({
            buttons: [
                {id: 'books', title: Ox._('Books')},
                {id: 'music', title: Ox._('Music'), disabled: true},
                {id: 'movies', title: Ox._('Movies'), disabled: true}
            ],
            style: 'squared',
            selectable: true,
            value: 'books'
        }).css({
            float: 'left',
            margin: '4px'
        })
        .bindEvent({
            change: function(data) {
                // ...
            }
        });

    return that;

};