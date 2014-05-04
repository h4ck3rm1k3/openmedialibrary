this.txtjs = {};

txtjs.open = function(url) {
    Ox.load(function() {
        Ox.get(url, function(text) {
            var $body = Ox.$('body')
                    .css({
                        backgroundColor: 'rgb(255, 255, 255)'
                    }),
                $text = Ox.$('<div>')
                    .css({
                        padding: '10% 20% 10% 10%',
                        fontFamily: 'Georgia, Palatino, DejaVu Serif, Book Antiqua, Palatino Linotype, Times New Roman, serif',
                        fontSize: '20px',
                        lineHeight: '30px'
                    })
                    .appendTo($body),
                $scroll = Ox.$('<div>')
                    .css({
                        position: 'fixed',
                        right: '24px',
                        top: '16px',
                        width: '7%',
                        bottom: '16px',
                        overflow: 'hidden'
                    })
                    .appendTo($body),
                $scrollText = Ox.$('<div>')
                    .css({
                        fontSize: '2px',
                        lineHeight: '3px',
                        WebkitUserSelect: 'none'
                    })
                    .on({
                        click: function(e) {
                            var offset = 'offsetY' in e ? e.offsetY : e.layerY;
                            document.body.scrollTop = offset / factor;
                            Ox.print('!', offset)
                        }
                    })
                    .appendTo($scroll),
                scale;
            text = Ox.encodeHTMLEntities(text)
                .replace(/\r\n/g, '\n')
                .replace(/\n/g, '<br>');
            $text.html(text);
            $scrollText.html(text);
            var textHeight = $text[0].clientHeight,
                scrollTextHeight = $scrollText[0].clientHeight,
                factor = scrollTextHeight / textHeight;
            window.onscroll = function() {
                $scroll[0].scrollTop = window.pageYOffset * factor;
            };
        });
    });
};

