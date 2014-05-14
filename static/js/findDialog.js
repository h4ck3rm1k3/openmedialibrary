'use strict';

oml.ui.findDialog = function() {

    var ui = oml.user.ui,

        that = Ox.Dialog({
            buttons: [
                Ox.Button({
                    id: 'done',
                    title: Ox._('Done')
                })
                .bindEvent({
                    click: function() {
                        var list = oml.$ui.findForm.getList();
                        if (list.save) {
                            oml.addList({
                                name: list.name,
                                query: list.query
                            });
                        }
                        that.close()
                    }
                })
            ],
            closeButton: true,
            content: oml.$ui.findForm = oml.ui.findForm()
                .css({margin: '16px'}),
            fixedSize: true,
            height: 264,
            removeOnClose: true,
            title: Ox._('Advanced Find'),
            width: 648 + Ox.UI.SCROLLBAR_SIZE
        }),

        $updateCheckbox = Ox.Checkbox({
                title: Ox._('Update Results in the Background'),
                value: oml.user.ui.updateAdvancedFindResults
            })
            .css({
                float: 'left',
                margin: '4px'
            })
            .bindEvent({
                change: function(data) {
                    oml.UI.set({updateAdvancedFindResults: data.value});
                    //data.value && oml.$ui.findForm.updateResults();
                }
            });

    $($updateCheckbox.find('.OxButton')[0]).css({margin: 0});
    $(that.find('.OxBar')[1]).append($updateCheckbox);

    return that;

};