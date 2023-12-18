
frappe.query_reports["Sales Summary Report"] = {
	onload: function(report) {
		report.page.add_inner_button ("Preview Report", function () {
			frappe.query_report.refresh();
		});
		
	},
	"filters": [
		{
			fieldname: "company",
			label: "Company",
			fieldtype: "Link",
			options:"Company",
			on_change: function (query_report) {},
			default:frappe.defaults.get_user_default("Company"),
		},
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
			"fieldname": "price_list",
			"label": __("Sale Type"),
			"fieldtype": "MultiSelectList",
			on_change: function (query_report) {},
			get_data: function(txt) {
				return frappe.db.get_link_options('Price List', txt,{"selling":1});
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
		{
			"fieldname": "customer_group",
			"label": __("Customer Group"),
			"fieldtype": "MultiSelectList",
			on_change: function (query_report) {},
			get_data: function(txt) {
				return frappe.db.get_link_options('Customer Group', txt,{"is_group":0});
			}
		},
		{
			"fieldname": "supplier_group",
			"label": __("Supplier Group"),
			"fieldtype": "MultiSelectList",
			on_change: function (query_report) {},
			get_data: function(txt) {
				
				return frappe.db.get_link_options('Supplier Group', txt,{"is_group":0});
			}
		},
		{
			"fieldname": "supplier",
			"label": __("Supplier"),
			"fieldtype": "MultiSelectList",
			on_change: function (query_report) {},
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
			on_change: function (query_report) {},
			"options": "\nCategory\nProduct Group\nBrand\nCompany\nBranch\nSale Type\nPOS Profile\nCustomer\nCustomer Group\nMembership\nTerritory\nSupplier\nSupplier Group\nWarehouse\nDate\n\Month\nYear\nSale Invoice",
			
		},
		{
			"fieldname": "row_group",
			"label": __("Row Group By"),
			"fieldtype": "Select",
			on_change: function (query_report) {},
			"options": "Product\nCategory\nProduct Group\nBrand\nCompany\nBranch\nSale Type\nPOS Profile\nCustomer\nCustomer Group\nMembership\nTerritory\nSupplier\nSupplier Group\nWarehouse\nDate\n\Month\nYear\nSale Invoice",
			"default":"Category"
		},
		{
			"fieldname": "column_group",
			"label": __("Column Group By"),
			"fieldtype": "Select",
			on_change: function (query_report) {},
			"options": "None\nDaily\nWeekly\nMonthly\nQuarterly\nHalf Yearly\nYearly",
			"default":"None"
		},
		{
			"fieldname": "hide_columns",
			"label": __("Hide Columns"),
			"fieldtype": "MultiSelectList",
			on_change: function (query_report) {},
			get_data: function(txt) {
				return [
					{"value":"Amount","description":"Amount"},
					{"value":"Transaction","description":"Transaction"},
					{"value":"Quantity","description":"Quantity"},
					{"value":"Sub Total","description":"Sub Total"},
					{"value":"Cost","description":"Cost"},
					{"value":"Profit","description":"Profit"},
					{"value":"Total Discount","description":"Total Discount"},
				]
			},
			"default":"All"
		},
		{
			"fieldname": "chart_type",
			"label": __("Chart Type"),
			"fieldtype": "Select",
			"options": "None\nbar\nline",
			on_change: function (query_report) {},
			"d,efault":"bar"
		},
		{
			"fieldname": "status",
			"label": __("Status"),
			"fieldtype": "MultiSelectList",
			on_change: function (query_report) {},
			get_data: function(txt) {
				return [
					{"value":"Draft","description":"Draft"},
					{"value":"Return","description":"Return"},
					{"value":"Credit Note Issued","description":"Credit Note Issued"},
					{"value":"Consolidated","description":"Consolidated"},
					{"value":"Submitted","description":"Submitted"},
					{"value":"Paid","description":"Profit"},
					{"value":"Unpaid","description":"Unpaid"},
					{"value":"Unpaid and Discounted","description":"Unpaid and Discounted"},
					{"value":"Overdue and Discounted","description":"Overdue and Discounted"},
					{"value":"Overdue","description":"Overdue"},
					{"value":"Cancelled","description":"Cancelled"},
					{"value":"Internal Transfer","description":"Internal Transfer"},
				]
			},
		}
	],
	"formatter": function(value, row, column, data, default_formatter) {
	
		value = default_formatter(value, row, column, data);

		if (data && data.is_group==1) {
			value = $(`<span>${value}</span>`);

			var $value = $(value).css("font-weight", "bold");
			

			value = $value.wrap("<p></p>").parent().html();
		}

		return value;
	},
};

 