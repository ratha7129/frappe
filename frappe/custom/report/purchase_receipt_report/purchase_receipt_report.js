// Copyright (c) 2022, Frappe Technologies and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Purchase Receipt Report"] = {
	"filters": [
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "MultiSelectList",
			get_data: function(txt) {
				
				return frappe.db.get_link_options('Company', txt);
			}
		},
		{
			"fieldname": "warehouse",
			"label": __("Warehouse"),
			"fieldtype": "MultiSelectList",
			get_data: function(txt) {
				group = frappe.query_report.get_filter_value("company");
				if(group==""){
					return frappe.db.get_link_options('Warehouse', txt,{"is_group":0});
				}
				else {
					return frappe.db.get_link_options('Warehouse', txt,filters={
						is_group:0,
						"company":["in",group]
					});
				}
			}
		},
		{
			fieldname: "start_date",
			label: "Start Date",
			fieldtype: "Date",
			default:frappe.datetime.nowdate()
		},
		{
			fieldname: "end_date",
			label: "End Date",
			fieldtype: "Date",
			default:frappe.datetime.nowdate()
		},
		{
			"fieldname": "supplier_group",
			"label": __("Supplier Group"),
			"fieldtype": "MultiSelectList",
			get_data: function(txt) {
				
				return frappe.db.get_link_options('Supplier Group', txt,{"is_group":0});
			}
		},
		{
			"fieldname": "supplier",
			"label": __("Supplier"),
			"fieldtype": "MultiSelectList",
			get_data: function(txt) {
				group = frappe.query_report.get_filter_value("supplier_group");
				if(group==""){
					return frappe.db.get_link_options('Supplier', txt);
				}
				else {
					return frappe.db.get_link_options('Supplier', txt,filters={
						"supplier_group":["in",group]
					});
				}
			}
		},
		{
			fieldname: "status",
			label: "Status",
			fieldtype: "MultiSelectList",
			get_data: function(txt) {
				return [
					{"value":"Completed","description":""},
					{"value":"To Bill","description":""},
					{"value":"Cancelled","description":""},
				]
			},
		},
	],
	"formatter": function(value, row, column, data, default_formatter) {
	
		value = default_formatter(value, row, column, data);

		if (data && data.is_group==1) {
			value = $(`<span>${value}</span>`);
			var $value = $(value).css("font-weight", "bold");
			value = $value.wrap("<p></p>").parent().html();
		}

		if(value == 'Completed'){
			value = $(`<span>${value}</span>`);
			var $value = $(value).css("color", "#06BD00");
			value = $value.wrap("<p></p>").parent().html();
		}
		if(value == 'Cancelled'){
			value = $(`<span>${value}</span>`);
			var $value = $(value).css("color", "#E20000");
			value = $value.wrap("<p></p>").parent().html();
		}
		return value;
	},
};
