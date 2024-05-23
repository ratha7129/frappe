// Copyright (c) 2022, Frappe Technologies and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Product List"] = {
	"filters": [
		{
			fieldname: "warehouse",
			label: "Warehouse",
			fieldtype: "MultiSelectList",
			get_data: function(txt) {
				return frappe.db.get_link_options('Warehouse', txt,{"is_group":0});
			}
		},
		{
			fieldname: "parent_item_group",
			label: "Parent Item Group",
			fieldtype: "MultiSelectList",
			get_data: function(txt) {
				return frappe.db.get_link_options('Item Group', txt,{"is_group":1});
			}
		},
		{
			fieldname: "item_group",
			label: "Item Group",
			fieldtype: "MultiSelectList",
			get_data: function(txt) {
				return frappe.db.get_link_options('Item Group', txt,{"is_group":0});
			}
		},
		{
			fieldname: "supplier",
			label: "Supplier",
			fieldtype: "MultiSelectList",
			get_data: function(txt) {
				return frappe.db.get_link_options('Supplier', txt);
			}
		},
		{
			fieldname: "allow_discount",
			label: "Allow Discount",
			fieldtype: "Select",
			default:"All",
			options: [
				   	{"value":"All"},
					{"value":"Yes"},
					{"value":"No"}
				]
		},
	]
};
