'use strict';

oml.ui.previewDialog = function() {

    var ui = oml.user.ui,

        $image,
        $list = oml.$ui.list,
        item = Ox.last($list.options('selected')),
        coverRatio = $list.value(item, 'coverRatio') || oml.config.coverRatio,
        size = getSize(coverRatio),

        that = Ox.Dialog({
            closeButton: true,
            content: Ox.Element(),
            fixedRatio: true,
            focus: false,
            height: size.height,
            maximizeButton: true,
            title: Ox._('Loading...'),
            width: size.width
        })
        .bindEvent({
            resize: function(data) {
                $image.css({
                    width: data.width,
                    height: data.height
                });
            },
            oml_find: function() {
                that.close();
            },
            oml_item: function() {
                that.close();
            },
            oml_page: function() {
                that.close();
            }
        });

    function getSize(posterRatio) {
        var windowWidth = window.innerWidth * 0.8,
            windowHeight = window.innerHeight * 0.8,
            windowRatio = windowWidth / windowHeight;
        return {
            width: Math.round(
                posterRatio > windowRatio ? windowWidth : windowHeight * posterRatio
            ),
            height: Math.round(
                posterRatio < windowRatio ? windowHeight : windowWidth / posterRatio
            )
        };
    }

    that.update = function() {
        oml.api.get({
            id: Ox.last($list.options('selected')),
            keys: ['coverRatio', 'id', 'modified', 'title']
        }, function(result) {
            var item = result.data,
                coverRatio = item.coverRatio,
                size = getSize(coverRatio),
                title = Ox.encodeHTMLEntities(item.title);
            $image = $('<img>')
                .attr({
                    src: '/' + item.id + '/cover128.jpg?' + item.modified
                })
                .css({
                    width: size.width + 'px',
                    height: size.height + 'px'
                });
            $('<img>')
                .load(function() {
                    $image.attr({
                        src: $(this).attr('src')
                    });
                })
                .attr({
                    src: '/' + item.id + '/cover1024.jpg?' + item.modified
                });
            that.options({
                    content: $image,
                    title: title,
                })
                .setSize(size.width, size.height);
        });
        return that;
    };

    return that.update();

};
