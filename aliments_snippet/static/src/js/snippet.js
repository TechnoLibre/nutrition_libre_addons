odoo.define('aliments_snippet.snippets', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');

    publicWidget.registry.AlimentsSnippet = publicWidget.Widget.extend({
        selector: '.aliments-list',
        start: function () {
            var self = this;
            this.getAliments();
            this.$el.find('#add-aliment-form').on('submit', function (e) {
                e.preventDefault();
                self.addAliment();
            });
        },
        getAliments: function () {
            var self = this;
            this._rpc({
                route: '/aliments/get_list',
            }).then(function (result) {
                var aliments = JSON.parse(result);
                var html = '<ul class="list-group">';
                aliments.forEach(function (aliment) {
                    html += '<li class="list-group-item">' + aliment.name + '</li>';
                });
                html += '</ul>';
                self.$el.find('#aliments-container').html(html);
            });
        },
        addAliment: function () {
            var self = this;
            var name = this.$el.find('#new-aliment-name').val();
            this._rpc({
                route: '/aliments/add',
                params: {
                    name: name,
                },
            }).then(function (result) {
                var response = JSON.parse(result);
                if (response.success) {
                    self.getAliments();
                    self.$el.find('#new-aliment-name').val('');
                }
            });
        },
    });
});
