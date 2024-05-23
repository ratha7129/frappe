# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	return get_columns(filters), get_report_data(filters)

def get_columns(filters):
	columns = []
	columns.append({'fieldname':'parent_item_group','label':"Parent Item Group",'fieldtype':'Data','align':'left','width':150})
	columns.append({'fieldname':'item_group','label':"Item Group",'fieldtype':'Data','align':'left','width':150})
	columns.append({'fieldname':'available_branch','label':"Available Branch",'fieldtype':'Data','align':'left','width':180	})
	columns.append({'fieldname':'supplier','label':"Supplier",'fieldtype':'Data','align':'left','width':150	})
	columns.append({'fieldname':'item_code','label':"Barcode",'fieldtype':'Data','align':'left','width':150})
	columns.append({'fieldname':'item_name','label':"Description",'fieldtype':'Data','align':'left','width':400})
	columns.append({'fieldname':'min_quantity','label':"Min. QTY",'fieldtype':'Data','align':'center','width':70})
	columns.append({'fieldname':'max_quantity','label':"Max. QTY",'fieldtype':'Data','align':'center','width':70})
	columns.append({'fieldname':'actual_qty','label':"QTY",'fieldtype':'Data','align':'center','width':70})
	columns.append({'fieldname':'cost','label':"Cost",'fieldtype':'Currency','align':'left','width':90})
	columns.append({'fieldname':'price','label':"R.Price",'fieldtype':'Currency','align':'left','width':90})
	columns.append({'fieldname':'whole_sale','label':"W.Price",'fieldtype':'Currency','align':'left','width':90})
	columns.append({'fieldname':'allow_discount','label':"Allow Discount",'fieldtype':'Check','align':'center','width':120})
	return columns
def get_report_data(filters):
	warehouse = ""
	item_group = ""
	supplier = ""
	parent_item_group = ""
	if filters.get("warehouse"): warehouse = " and f.warehouse in (" + get_list(filters,"warehouse") + ")"
	if filters.get("parent_item_group"): parent_item_group = " and b.parent_item_group in (" + get_list(filters,"parent_item_group") + ")"
	if filters.get("item_group"): item_group = " and a.item_group in (" + get_list(filters,"item_group") + ")"
	if filters.get("supplier"): supplier = " and a.supplier in (" + get_list(filters,"supplier") + ")"
	sql = """
	SELECT 
		a.item_group,
		b.parent_item_group,
		a.item_code,
		a.item_name,
		a.stock_uom,
		coalesce(a.supplier,'No Supplier') supplier,
		coalesce((SELECT GROUP_CONCAT(branch SEPARATOR ', ') FROM `tabBranch Items` g WHERE g.parent = a.item_code GROUP BY g.parent),"All") available_branch,
		(SELECT coalesce(sum(actual_qty),0) FROM `tabBin` f WHERE f.item_code = a.item_code AND f.stock_uom = a.stock_uom  {0} {1}) actual_qty,
		coalesce((SELECT price_list_rate FROM `tabItem Price` c WHERE item_code = a.item_code AND c.uom = a.stock_uom AND price_list = 'Standard Selling' LIMIT 1),0) price,
		coalesce((SELECT price_list_rate FROM `tabItem Price` d WHERE item_code = a.item_code AND d.uom = a.stock_uom AND price_list = 'Wholesale Price' LIMIT 1),0) whole_sale,
		coalesce((SELECT price_list_rate FROM `tabItem Price` e WHERE item_code = a.item_code AND e.uom = a.stock_uom AND price_list = 'Standard Buying' LIMIT 1),0) cost,
		a.allow_discount,
		a.max_quantity,
		a.min_quantity
	FROM `tabItem` a 
	inner join `tabItem Group` where b.name = a.item_group
	WHERE a.allow_discount = if('{2}'='All',a.allow_discount,if('{2}'='Yes',1,0)) {1} {4} {3}
	""".format(warehouse, item_group,filters.allow_discount,supplier,parent_item_group)
	data = frappe.db.sql(sql,as_dict=1)
	return data

def get_list(filters,name):
	data = ','.join("'{0}'".format(x) for x in filters.get(name))
	return data