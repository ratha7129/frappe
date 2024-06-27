# Copyright (c) 2024, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):

	return get_columns(), get_data(filters)

def get_columns():
	columns = []
	columns.append({'fieldname':'item_code','label':"Item Code",'fieldtype':'Data','options':'Sales Invoice','align':'left','width':150})
	columns.append({'fieldname':'item_name','label':"Item Name",'fieldtype':'Data','options':'Sales Invoice','align':'left','width':250})
	columns.append({'fieldname':'pos_profile','label':"POS Profile",'fieldtype':'Data','options':'Sales Invoice','align':'left','width':250})
	columns.append({'fieldname':'parent_item_group','label':"Item Group",'fieldtype':'Data','options':'Sales Invoice','align':'left','width':250})
	columns.append({'fieldname':'item_group','label':"Item Category",'fieldtype':'Data','options':'Sales Invoice','align':'left','width':250})
	columns.append({'fieldname':'TRANSACTION','label':"Transaction",'fieldtype':'Data','options':'Sales Invoice','align':'center','width':100})
	columns.append({'fieldname':'month','label':"Month",'fieldtype':'Data','options':'Sales Invoice','align':'center','width':100})
	columns.append({'fieldname':'qty','label':"QTY",'fieldtype':'Data','options':'Sales Invoice','align':'center','width':100})
	columns.append({'fieldname':'sub_total','label':"Sub Total",'fieldtype':'Currency','options':'Sales Invoice','align':'right','width':100})
	columns.append({'fieldname':'cost','label':"Cost",'fieldtype':'Currency','options':'Sales Invoice','align':'right','width':100})
	columns.append({'fieldname':'tax','label':"Tax",'fieldtype':'Currency','options':'Sales Invoice','align':'right','width':100})
	columns.append({'fieldname':'grand_total','label':"Grand Total",'fieldtype':'Currency','options':'Sales Invoice','align':'right','width':100})
	columns.append({'fieldname':'profit','label':"Profit",'fieldtype':'Currency','options':'Sales Invoice','align':'right','width':100})
	return columns

def get_data(filters):
	sql = """WITH item_transaction AS(
			SELECT 
			item_code,
			sum(transaction) TRANSACTION
			FROM (SELECT
			item_code,
			COUNT(DISTINCT(a.name)) transaction
			FROM `tabPOS Invoice Item` a
			INNER JOIN `tabPOS Invoice` b ON b.name = a.parent
			WHERE STATUS='Consolidated' AND posting_date BETWEEN '{1}' AND '{2}'
			GROUP BY item_code
			union all
			SELECT
			item_code,
			COUNT(DISTINCT(a.name)) transaction
			FROM `tabSales Invoice Item` a
			INNER JOIN `tabSales Invoice` b ON b.name = a.parent
			WHERE is_consolidated = 0 AND posting_date BETWEEN '{1}' AND '{2}'
			GROUP BY item_code)a
			GROUP BY item_code)
			SELECT
				a.item_code,
				a.item_name,
				b.pos_profile,
				a.parent_item_group,
				a.item_group,
				coalesce(c.transaction,0) TRANSACTION,
				date_format(b.posting_date,'%%Y/%%m') month,
				sum(a.qty*a.conversion_factor) qty,
				sum(a.base_price_list_rate * a.qty) sub_total,
				sum(a.base_price_list_rate*a.qty-a.net_amount) discount,
				sum(a.qty*d.valuation_rate*a.conversion_factor) cost,
				sum(coalesce(a.item_tax,0)) tax,
				sum(a.net_amount) grand_total,
				sum(a.net_amount + coalesce(a.item_tax,0) - (a.qty*d.valuation_rate*a.conversion_factor)) profit
			FROM `tabSales Invoice Item` AS a
			INNER JOIN `tabSales Invoice` b on b.name = a.parent
			left join item_transaction c on c.item_code = a.item_code
			left join `tabItem` d ON d.item_code = a.item_code
			WHERE
				b.docstatus in (1) 
				{0}
			GROUP by
			a.item_code,
			a.item_name,
			a.parent_item_group,
			a.item_group,
			coalesce(c.transaction,0),
			date_format(b.posting_date,'%%Y/%%m'),
			b.pos_profile
			ORDER BY 
			date_format(b.posting_date,'%%Y/%%m'),
			a.item_code,
			a.item_name""".format(get_conditions(filters),filters["start_date"],filters["end_date"])
	data = frappe.db.sql(sql,filters, as_dict=0)
	return data

def get_conditions(filters):

	conditions = " and b.posting_date between %(start_date)s AND %(end_date)s"
	 
	if filters.get("item_group"):
		conditions += " AND a.parent_item_group in %(item_group)s"

	if filters.get("item_category"):
		conditions += " AND a.item_group in %(item_category)s"
		
	if filters.get("branch"):
		conditions += " AND b.branch in %(branch)s"
	
	if filters.get("pos_profile"):
		conditions += " AND b.pos_profile in %(pos_profile)s"
		
	return conditions