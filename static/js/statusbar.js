'use strict';

oml.ui.statusbar = function() {

    var ui = oml.user.ui,

        $text = {
            titleTotal: Ox.Element('<span>').html(Ox._('Total: ')),
            total: Ox.Element('<span>'),
            titleSelected: Ox.Element('<span>').html(' &mdash; ' + Ox._('Selected: ')),
            selected: Ox.Element('<span>'),
            loading: Ox.Element('<span>').html(Ox._('Loading...'))
        },

        that = Ox.Bar({size: 16})
            .css({textAlign: 'center'})
            .append(
                Ox.Element()
                    .css({
                        margin: '2px 4px',
                        fontSize: '9px',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis'
                    })
                    .append($text.loading)
                    .append($text.titleTotal)
                    .append($text.total)
                    .append($text.titleSelected)
                    .append($text.selected)
            )
            .bindEvent({
                oml_listselection: function(data) {
                    // ...
                }
            });

    function getText(data) {
        return Ox.toTitleCase(Ox.formatCount(data.items, 'book')) + (
            data.items ? ', ' + Ox.formatValue(data.size, 'B') : ''
        );
    }

    that.set = function(key, data) {
        if (key == 'loading') {
            Ox.forEach($text, function($element, key) {
                $element[key == 'loading' ? 'show' : 'hide']();
            });
        } else {
            $text.loading.hide();
            if (key == 'selected') {
                if (data.items == 0) {
                    $text.titleTotal.hide();
                    $text.titleSelected.hide();
                    $text.selected.hide();
                } else {
                    $text.titleTotal.show();
                    $text.titleSelected.show();
                    $text.selected.html(getText(data)).show();
                }
            } else {
                $text.total.html(getText(data)).show();
            }
        }
    };

    that.set('loading');

    return that;

};