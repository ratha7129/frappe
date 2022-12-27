// Copyright (c) 2022, Frappe Technologies and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Sales Product Quantity Summary Report"] =  {
	"filters": [
		{
			fieldname: "company",
			label: "Company",
			fieldtype: "Link",
			options:"Company",
			reqd: 1,
			default:frappe.defaults.get_user_default("Company"),
		},
		{
			fieldname: "start_date",
			label: "Start Date",
			fieldtype: "Date",
			default:frappe.datetime.month_start()
		},
		{
			fieldname: "end_date",
			label: "End Date",
			fieldtype: "Date",
			default:frappe.datetime.month_end()
		},
		{
			fieldname: "branch",
			label: "Branch",
			"fieldtype": "MultiSelectList",
			get_data: function(txt) {
				return frappe.db.get_link_options('Branch', txt);
			}
		},
		// {
		// 	"fieldname": "price_list",
		// 	"label": __("Sale Type"),
		// 	"fieldtype": "MultiSelectList",
		// 	get_data: function(txt) {
		// 		return frappe.db.get_link_options('Price List', txt,{"selling":1});
		// 	}
		// },
		{
			"fieldname": "item_group",
			"label": __("Item Group"),
			"fieldtype": "MultiSelectList",
			get_data: function(txt) {
				
				return frappe.db.get_link_options('Item Group', txt,{"is_group":1});
			}
		},
		{
			"fieldname": "item_category",
			"label": __("Item Category"),
			"fieldtype": "MultiSelectList",
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
			"fieldname": "parent_row_group",
			"label": __("Parent Group By"),
			"fieldtype": "Select",
			"options": "\nCategory\nProduct Group\nBranch\nDate\n\Month\nYear",
			
		},
		{
			"fieldname": "row_group",
			"label": __("Row Group By"),
			"fieldtype": "Select",
			"options": "Product\nCategory\nProduct Group\nDate\n\Month\nYear",
			"default":"Category"
		},
		{
			"fieldname": "column_group",
			"label": __("Column Group By"),
			"fieldtype": "Select",
			"options": "None\nDaily\nWeekly\nMonthly\nQuarterly\nHalf Yearly\nYearly",
			"default":"None"
		},
		// {
		// 	"fieldname": "chart_type",
		// 	"label": __("Chart Type"),
		// 	"fieldtype": "Select",
		// 	"options": "None\nbar\nline",
		// 	"d,efault":"bar"
		// }
	],
	"formatter": function(value, row, column, data, default_formatter) {
		console.log(column)
		value = default_formatter(value, row, column, data);

		if (data && data.is_group==1) {
			value = $(`<span>${value}</span>`);

			var $value = $(value).css("font-weight", "bold");
			

			value = $value.wrap("<p></p>").parent().html();
		}

		return value;
	},
};

 