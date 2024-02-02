// Copyright (c) 2024, Frappe Technologies and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Sale Product Summary By Month"] = {
	onload: function(report) {
		report.page.add_inner_button ("Preview Report", function () {
			frappe.query_report.refresh();
		});
		report.page.add_inner_button ("Export Sheet", function () {
			frappe.call({
				method:
					"frappe.upload_to_googlesheet.upload_to_google_sheet",
				args: {
					start_date: frappe.query_report.get_filter_value("start_date"),
					end_date: frappe.query_report.get_filter_value("end_date"),
				},
				callback: (response) => {
					
				},
			});
		});
	},
	"filters": [
		{
			fieldname: "start_date",
			label: "Start Date",
			fieldtype: "Date",
			on_change: function (query_report) {},
			default:frappe.datetime.get_today()
		},
		{
			fieldname: "end_date",
			label: "End Date",
			fieldtype: "Date",
			on_change: function (query_report) {},
			default:frappe.datetime.get_today()
		},
		{
			fieldname: "branch",
			label: "Branch",
			"fieldtype": "MultiSelectList",
			on_change: function (query_report) {},
			get_data: function(txt) {
				return frappe.db.get_link_options('Branch', txt);
			}
		},
		{
			"fieldname": "item_group",
			"label": __("Item Group"),
			"fieldtype": "MultiSelectList",
			on_change: function (query_report) {},
			get_data: function(txt) {
				
				return frappe.db.get_link_options('Item Group', txt,{"is_group":1});
			}
		},
		{
			"fieldname": "item_category",
			"label": __("Item Category"),
			"fieldtype": "MultiSelectList",
			on_change: function (query_report) {},
			get_data: function(txt) {
				group = frappe.query_report.get_filter_value("item_group");
				if(group==""){
					return frappe.db.get_link_options('Item Group', txt,filters={
						is_group:0
					});
				}
				else {
					return frappe.db.get_link_options('Item Group', txt,filters={
						is_group:0,
						"parent_item_group":["in",group]
					});
				}
			}
		},
	]
};
