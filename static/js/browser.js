'use strict';

oml.ui.browser = function() {

    var ui = oml.user.ui,

        that = Ox.IconList({
            centered: true,
            defaultRatio: oml.config.iconRatio,
            draggable: true,
            item: function(data, sort, size) {
                var color = oml.getIconInfoColor(ui.iconInfo, data).map(function(rgb) {
                        return rgb.concat(0.8);
                    }),
                    ratio = (ui.icons == 'cover' ? data.coverRatio : data.previewRatio)
                        || oml.config.iconRatio,
                    width = Math.round(ratio >= 1 ? size : size * ratio),
                    height = Math.round(ratio <= 1 ? size : size / ratio),
                    sortKey = sort[0].key,
                    info = Ox.getObjectById(oml.config.sortKeys, sortKey).format(
                        Ox.contains(['title', 'random'], sortKey)
                        ? (data.author || '') : data[sortKey]
                    );
                size = size || 64;
                return {
                    extra: ui.showIconInfo ? $('<div>')
                        .css({
                            width: width + 'px',
                            height: Math.round(size / 12.8) + 'px',
                            borderWidth: Math.round(size / 64) + 'px 0',
                            borderStyle: 'solid',
                            borderColor: 'rgba(' + color[2].join(', ') + ')',
                            margin: Math.round(size / 18) + 'px ' + Math.round(width / 2 - 8) + 'px',
                            fontSize: Math.round(size / 16) + 'px',
                            textAlign: 'center',
                            color: 'rgba(' + color[2].join(', ') + ')',
                            backgroundImage: '-webkit-linear-gradient(top, ' + color.slice(0, 2).map(function(rgba) {
                                return 'rgba(' + rgba.join(', ') + ')';
                            }).join(', ') + ')',
                            WebkitTransform: 'rotate(45deg)'
                        })
                        .html(
                            ui.iconInfo == 'extension'
                            ? data.extension.toUpperCase()
                            : Ox.formatValue(data.size, 'B')
                        ) : null,
                    height: height,
                    id: data.id,
                    info: info,
                    title: data.title,
                    url: '/' + data.id + '/' + ui.icons + '128.jpg?' + data.modified,
                    width: width
                };
            },
            items: function(data, callback) {
                oml.api.find(Ox.extend(data, {
                    query: ui.find
                }), callback);
            },
            keys: [
                'author', 'coverRatio', 'extension', 'id', 'mediastate', 'modified',
                'previewRatio', 'size', 'textsize', 'title'
            ],
            max: 1,
            min: 1,
            orientation: 'horizontal',
            // FIXME: is this correct?:
            selected: ui.item ? [ui.item]
                : ui.listSelection.length ? [ui.listSelection[0]]
                : [],
            size: 64,
            sort: ui.listSort,
            unique: 'id'
        })
        .css({
            'overflow-y': 'hidden'
        })
        .bindEvent({
            key_control_delete: function() {
                var listData = oml.getListData();
                if (listData.own) {
                    oml.ui.deleteItemsDialog().open();
                }
            },
            open: function(data) {
                if (that.value(data.ids[0], 'mediastate') == 'available') {
                    oml.UI.set({itemView: 'book'});
                }
            },
            select: function(data) {
                oml.UI.set({
                    item: data.ids[0],
                    itemView: 'info',
                    listSelection: data.ids
                });
            },
            oml_find: function() {
                that.reloadList();
            },
            oml_iconinfo: function() {
                that.reloadList(true);
            },
            oml_icons: function() {
                that.reloadList(true);
            },
            oml_showiconinfo: function() {
                that.reloadList(true);
            },
            oml_item: function(data) {
                if (data.value && !data.previousValue) {
                    that.gainFocus();
                }
            },
            oml_listselection: function(data) {
                if (data.value.length) {
                    that.options({selected: [data.value[0]]});
                }
            },
            oml_listsort: function(data) {
                that.options({sort: data.value});
            },
            oml_sidebarsize: function(data) {
                that.size(); // FIXME: DOESN'T CENTER
            }
        });

    oml.enableDragAndDrop(that);

    return that;

};
