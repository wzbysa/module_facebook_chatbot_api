odoo.define('module_api_attendances.create_noc_button', function (require){
"use strict";

var core = require('web.core');
var CalendarView = require('web_calendar.CalendarView');
var QWeb = core.qweb;

CalendarView.include({

    render_buttons: function($node) {
        var self = this;
        this._super($node);
        this.$buttons.find('.o_list_tender_button_service_noc').click(this.proxy('service_noc_action'));
        console.log("Hello world!");
        },

    service_noc_action: function () {
        var self = this;
        self.do_action('module_api_attendances.action_service_noc_working_time_wizard');
        },

    });
});
