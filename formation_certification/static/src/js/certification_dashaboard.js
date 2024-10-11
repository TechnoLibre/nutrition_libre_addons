odoo.define('harmonie_certification.dashboard', function (require) {
"use strict";

var AbstractAction = require('web.AbstractAction');
var core = require('web.core');

var CertificationDashboard = AbstractAction.extend({
    template: 'HarmonieCertificationDashboard',
    events: {
        'click .o_certification_action': '_onCertificationActionClick',
    },

    start: function() {
        return this._super.apply(this, arguments).then(this._loadDashboardData);
    },

    _loadDashboardData: function() {
        var self = this;
        return this._rpc({
            model: 'formation.certification',
            method: 'get_dashboard_data',
        }).then(function(result) {
            self.$el.find('.o_certification_count').text(result.total_certifications);
            self.$el.find('.o_certification_draft').text(result.draft_certifications);
            self.$el.find('.o_certification_sent').text(result.sent_certifications);
        });
    },

    _onCertificationActionClick: function(ev) {
        ev.preventDefault();
        var actionName = $(ev.currentTarget).data('action');
        this.do_action(actionName);
    },
});

core.action_registry.add('certification_dashboard', CertificationDashboard);

return CertificationDashboard;

});