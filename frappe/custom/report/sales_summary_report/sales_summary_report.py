# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt


from email import message
from dataclasses import field, fields
from email.errors import MessageParseError
from fnmatch import filter
from importlib.metadata import files
from socket import MsgFlag
import frappe
from frappe.utils import date_diff
import json

from frappe.utils.data import strip

def execute(filters=None):
	
 
	validate(filters)
	update_sale()
	
	
	report_data = []
	skip_total_row=False
	message=None
	if filters.get("parent_row_group"):
		report_data = get_report_group_data(filters)
		message="Enable <strong>Parent Row Group</strong> making report loading slower. Please try  to select some report filter to reduce record from database "
		skip_total_row = True
	else:
		report_data = get_report_data(filters)

	report_chart = None
	if filters.chart_type !="None" and len(report_data)<=100:
		report_chart = get_report_chart(filters,report_data)

	return get_columns(filters), report_data, message, report_chart, get_report_summary(report_data,filters),skip_total_row




def validate(filters):

	if filters.start_date and filters.end_date:
		if filters.start_date > filters.end_date:

			frappe.throw("The 'Start Date' ({}) must be before the 'End Date' ({})".format(filters.start_date, filters.end_date))

	
	if filters.column_group=="Daily":
		n = date_diff(filters.end_date, filters.start_date)
		if n>30:
			frappe.throw("Date range cannot greater than 30 days")

	if filters.row_group and filters.parent_row_group:
		if(filters.row_group == filters.parent_row_group):
			frappe.throw("Parent row group and row group can not be the same")

def update_sale():

	#update transaction to tbl sale invoice item
	sale_invoices = frappe.db.sql("select distinct parent from `tabSales Invoice Item` where total_transaction=0", as_dict=1)
	
	if sale_invoices:
		for s in sale_invoices:
			 
			item_count = frappe.db.sql("select count(name) as total from `tabSales Invoice Item` where parent='{}'".format(s["parent"]), as_dict=1)
			
			if item_count:
				total_item = item_count[0]["total"]
				#get total transaction from pos invoice
				pos_invoice_count = frappe.db.sql("select count(name) as total from `tabPOS Invoice` where consolidated_invoice='{}'".format(s["parent"]), as_dict=1)
				total_pos_invoice = 1
				if pos_invoice_count and pos_invoice_count[0]["total"]>1:
						total_pos_invoice = pos_invoice_count[0]["total"]

				sql = "update `tabSales Invoice Item` set total_transaction = {} where parent='{}'".format(total_pos_invoice/total_item, s["parent"])
				 
				frappe.db.sql(sql)
	
	frappe.db.commit()
	#end update total transaction to sale invoice item		

def get_columns(filters):
	
	columns = []
	columns.append({'fieldname':'row_group','label':filters.row_group,'fieldtype':'Data','align':'left','width':250})
	if filters.row_group == "Product":
		columns.append({"label":"Group Name","fieldname":"parent_item_group","fieldtype":"Data","align":"left",'width':130})
		columns.append({"label":"Category Name","fieldname":"item_group","fieldtype":"Data","align":"left",'width':130})
		columns.append({"label":"Item Code","fieldname":"item_code","fieldtype":"Data","align":"left",'width':130})
	hide_columns = filters.get("hide_columns")
	 
	if filters.column_group !="None" and filters.row_group not in ["Date","Month","Year"]:
		 
		for c in get_dynamic_columns(filters):
			columns.append(c)

	#add total to last column

	fields = get_report_field(filters)
	for f in fields:
		if not hide_columns or  f["label"] not in hide_columns:
			columns.append({
					'fieldname':"total_" +  f['fieldname'],
					'label':"Total " + f["label"],
					'fieldtype':f['fieldtype'],
					'precision': f["precision"],
					'align':f['align']
					}
				)
	 
	return columns



def get_dynamic_columns(filters):
	hide_columns = filters.get("hide_columns")
	#dynmic report file
	fields = get_fields(filters)
	#static report field
	report_fields = get_report_field(filters)
	columns=[]
	for f in fields:
		for rf in report_fields:
			if not hide_columns or  rf["label"] not in hide_columns:
				columns.append({
					'fieldname':f["fieldname"] + "_" + rf["fieldname"],
					'label': f["label"] + " "  + rf["short_label"],
					'fieldtype':rf["fieldtype"],
					'precision': rf["precision"],
					'align':rf["align"]}
				)

		
	return columns

def get_fields(filters):
	sql=""
	
	if filters.column_group=="Daily":
		sql = """
			select 
				concat('col_',date_format(date,'%d_%m')) as fieldname, 
				date_format(date,'%d') as label ,
				min(date) as start_date,
				max(date) as end_date
			from `tabDates` 
			where date between '{}' and '{}'
			group by
				concat('col_',date_format(date,'%d_%m')) , 
				date_format(date,'%d')  	
		""".format(filters.start_date, filters.end_date)
	elif filters.column_group =="Monthly":
		sql = """
			select 
				concat('col_',date_format(date,'%m_%Y')) as fieldname, 
				date_format(date,'%b %y') as label ,
				min(date) as start_date,
				max(date) as end_date
			from `tabDates` 
			where date between '{}' and '{}'
			group by
				concat('col_',date_format(date,'%m_%Y')) , 
				date_format(date,'%b %y')  	
		""".format(filters.start_date, filters.end_date)
	elif filters.column_group=="Weekly":
		sql = """
			select 
				concat('col_',date_format(date,'%v_%Y')) as fieldname, 
				concat('WK ',date_format(date,'%v %y')) as label ,
				min(date) as start_date,
				max(date) as end_date
			from `tabDates` 
			where date between '{}' and '{}'
			group by
				concat('col_',date_format(date,'%v_%Y')), 
				concat('WK ',date_format(date,'%v %y')) 
		""".format(filters.start_date, filters.end_date)
	elif filters.column_group=="Quarterly":
		sql = """
			select 
				concat('col_',QUARTER(date)) as fieldname, 
				concat('Q',QUARTER(date),' ',date_format(date,'%y')) as label ,
				min(date) as start_date,
				max(date) as end_date
			from `tabDates` 
			where date between '{}' and '{}'
			group by
				concat('col_',QUARTER(date)),
				concat('Q',QUARTER(date),' ',date_format(date,'%y')) 
		""".format(filters.start_date, filters.end_date)
	elif filters.column_group=="Half Yearly":
		sql = """
			select 
				concat('col_',if(month(date) between 1 and 6,'jan_jun','jul_dec'),date_format(date,'%y')) as fieldname, 
				concat(if(month(date) between 1 and 6,'Jan-Jun','Jul-Dec'),' ',date_format(date,'%y')) as label ,
				min(date) as start_date,
				max(date) as end_date
			from `tabDates` 
			where date between '{}' and '{}'
			group by
				concat('col_',if(month(date) between 1 and 6,'jan_jun','jul_dec'),date_format(date,'%y')), 
				concat(if(month(date) between 1 and 6,'Jan-Jun','Jul-Dec'),' ',date_format(date,'%y')) 
		""".format(filters.start_date, filters.end_date)
	elif filters.column_group=="Yearly":
		sql = """
			select 
				concat('col_',date_format(date,'%Y')) as fieldname, 
				date_format(date,'%Y') as label ,
				min(date) as start_date,
				max(date) as end_date
			from `tabDates` 
			where date between '{}' and '{}'
			group by
				concat('col_',date_format(date,'%Y')),
				date_format(date,'%Y')
		""".format(filters.start_date, filters.end_date)

	fields = frappe.db.sql(sql,as_dict=1)
	 
	return fields

def get_conditions(filters,group_filter=None):

	conditions = ""
	
	conditions += " b.company =if('{0}'='None',b.company,'{0}')".format(filters.company)
	if(group_filter!=None):
		conditions += " and {} ='{}'".format(group_filter["field"],group_filter["value"].replace("'","''").replace("%","%%"))
	
	conditions += " AND b.posting_date between %(start_date)s AND %(end_date)s"
	 
	if filters.get("item_group"):
		conditions += " AND a.parent_item_group in %(item_group)s"

	if filters.get("item_category"):
		conditions += " AND a.item_group in %(item_category)s"

	if filters.get("customer_group"):
		conditions += " AND b.customer_group in %(customer_group)s"

	if filters.get("price_list"):
		conditions += " AND b.selling_price_list in %(price_list)s"

	if filters.get("supplier"):
		conditions += " AND a.supplier in %(supplier)s"
	
	if filters.get("supplier_group"):
		conditions += " AND (SELECT supplier_group FROM `tabSupplier` b WHERE b.name = a.supplier) in %(supplier_group)s"
		
	if filters.get("branch"):
		conditions += " AND b.branch in %(branch)s"
	
	if filters.get("status"):
		conditions += " AND b.status in %(status)s"
		

	return conditions

def get_report_data(filters,parent_row_group=None,indent=0,group_filter=None):
	sql = ""
	hide_columns = filters.get("hide_columns")
	row_group = [d["fieldname"] for d in get_row_groups() if d["label"]==filters.row_group][0]
	if(parent_row_group!=None):
		row_group = [d["fieldname"] for d in get_row_groups() if d["label"]==parent_row_group][0]
	report_fields = get_report_field(filters)
	if(filters.parent_row_group is None and filters.row_group == "Product"):
		sql = """
		WITH item_transaction AS(
			SELECT 
			item_code,
			COUNT(TRANSACTION) TRANSACTION
			FROM (SELECT
			item_code,
			COUNT(DISTINCT(a.name)) transaction
			FROM `tabPOS Invoice Item` a
			INNER JOIN `tabPOS Invoice` b ON b.name = a.parent
			WHERE STATUS='Consolidated' AND posting_date BETWEEN '{0}' AND '{1}'
			GROUP BY item_code
			union all
			SELECT
			item_code,
			COUNT(DISTINCT(a.name)) transaction
			FROM `tabSales Invoice Item` a
			INNER JOIN `tabSales Invoice` b ON b.name = a.parent
			WHERE pos_profile is null AND posting_date BETWEEN '{0}' AND '{1}'
			GROUP BY item_code)a
			GROUP BY item_code)""".format(filters.start_date,filters.end_date)
	sql = sql + """ select {0} as row_group, {1} as indent """.format(row_group, indent)
	if filters.column_group != "None":
		fields = get_fields(filters)
		for f in fields:
			sql = strip(sql)
			if sql[-1]!=",":
				sql = sql + ','
			
			for rf in report_fields:
				if not hide_columns or  rf["label"] not in hide_columns:
					sql = sql +	"sum(if(b.posting_date between '{}' AND '{}',{},0)) as '{}_{}',".format(f["start_date"],f["end_date"],rf["sql_expression"].replace('sum',''),f["fieldname"],rf["fieldname"])
			#end for
	# total last column
	extra_group = ""
	if filters.row_group == "Product" or filters.parent_row_group == "Product":
		extra_group = ",a.item_code,a.item_group,a.parent_item_group,c.transaction"
	for rf in report_fields:
		#check sql variable if last character is , then remove it
		sql = strip(sql)
		
		if sql[-1]==",":
			sql = sql[0:len(sql)-1]
			 
		if not hide_columns or  rf["label"] not in hide_columns:
			sql = sql + " ,{} AS 'total_{}' ".format(rf["sql_expression"],rf["fieldname"])

	if(filters.parent_row_group is None and filters.row_group == "Product"):
		sql = sql + """ {2}
			FROM `tabSales Invoice Item` AS a
				INNER JOIN `tabSales Invoice` b on b.name = a.parent
				left join item_transaction c on c.item_code = a.item_code
				left join `tabItem` d ON d.item_code = a.item_code
			WHERE
				b.docstatus in (1) AND
				{0}
			GROUP BY 
			{1} {2}
		""".format(get_conditions(filters,group_filter), row_group,extra_group)
	else:
		sql = sql + """ {2}
			FROM `tabSales Invoice Item` AS a
				INNER JOIN `tabSales Invoice` b on b.name = a.parent
				left join `tabItem` d ON d.item_code = a.item_code
			WHERE
				b.docstatus in (1) AND
				{0}
			GROUP BY 
			{1} {2}
		""".format(get_conditions(filters,group_filter), row_group,extra_group)
	data = frappe.db.sql(sql,filters, as_dict=1)
	return data
 
def get_report_group_data(filters):
	parent = get_report_data(filters, filters.parent_row_group, 0)
	data=[]
 

	for p in parent:
		p["is_group"] = 1
		data.append(p)

		row_group = [d for d in get_row_groups() if d["label"]==filters.parent_row_group][0]
		children = get_report_data(filters, None, 1, group_filter={"field":row_group["fieldname"],"value":p[row_group["parent_row_group_filter_field"]]})
		for c in children:
			data.append(c)
	return data


def get_report_summary(data,filters):
	hide_columns = filters.get("hide_columns")
	report_summary=[]
	if filters.parent_row_group==None:
		report_summary =[{"label":"Total " + filters.row_group ,"value":len(data)}]
	
	fields = get_report_field(filters)

	for f in fields:
		if not hide_columns or  f["label"] not in hide_columns:
			value=sum(d["total_" + f["fieldname"]] for d in data if d["indent"]==0)
			if f["fieldtype"] == "Currency":
				value = frappe.utils.fmt_money(value)
			elif f["fieldtype"] =="Float":
				value = "{:.2f}".format(value)
			report_summary.append({"label":"Total {}".format(f["label"]),"value":value,"indicator":f["indicator"]})	

	return report_summary

def get_report_chart(filters,data):
	columns = []
	hide_columns = filters.get("hide_columns")
	dataset = []
	colors = []

	report_fields = get_report_field(filters)

	if filters.column_group != "None":
		fields = get_fields(filters)
		for f in fields:
			columns.append(f["label"])
		for rf in report_fields:
			if not hide_columns or  rf["label"] not in hide_columns:
				#loop sum dynamic column data data set value
				dataset_values = []
				for f in fields:
					dataset_values.append(sum(d["{}_{}".format(f["fieldname"],rf["fieldname"])] for d in data))
					
				dataset.append({'name':rf["label"],'values':dataset_values})
				colors.append(rf["chart_color"])

	else: # if column group is none
		for d in data:
			columns.append(d["row_group"])

		myds = []
		for rf in report_fields:
			if not hide_columns or  rf["label"] not in hide_columns:
				fieldname = 'total_'+rf["fieldname"]
				if(fieldname=="total_transaction"):
					dataset.append({'name':rf["label"],'values':(d["total_transaction"] for d in data)})
				elif(fieldname=="total_qty"):
					dataset.append({'name':rf["label"],'values':(d["total_qty"] for d in data)})
				elif(fieldname=="total_sub_total"):
					dataset.append({'name':rf["label"],'values':(d["total_sub_total"] for d in data)})
				elif(fieldname=="total_cost"):
					dataset.append({'name':rf["label"],'values':(d["total_cost"] for d in data)})
				elif(fieldname=="total_amount"):
					dataset.append({'name':rf["label"],'values':(d["total_amount"] for d in data)})
				elif(fieldname=="total_profit"):
					dataset.append({'name':rf["label"],'values':(d["total_profit"] for d in data)})

		 

	chart = {
		'data':{
			'labels':columns,
			'datasets':dataset
		},
		"type": filters.chart_type,
		"lineOptions": {
			"regionFill": 1,
		},
		"axisOptions": {"xIsSeries": 1}
	}
	return chart

def get_report_field(filters):
	if filters.parent_row_group == "Sale Invoice" or filters.row_group == "Sale Invoice" :
		return [
			{"label":"Quantity","short_label":"Qty", "fieldname":"qty","fieldtype":"Float","indicator":"Grey","precision":2, "align":"center","chart_color":"#FF8A65","sql_expression":"sum(a.qty*a.conversion_factor)"},
			{"label":"Sub Total", "short_label":"Sub To.", "fieldname":"sub_total","fieldtype":"Currency","indicator":"Grey","precision":None, "align":"right","chart_color":"#dd5574","sql_expression":"sum(a.base_price_list_rate * a.qty)"},
			{"label":"Discount", "short_label":"Disc.", "fieldname":"discount_amount","fieldtype":"Currency","indicator":"Grey","precision":None, "align":"right","chart_color":"#dd5574","sql_expression":"sum(a.base_price_list_rate*a.qty-a.net_amount)"},
			{"label":"Cost","short_label":"Cost", "fieldname":"cost","fieldtype":"Currency","indicator":"Blue","precision":None, "align":"right","chart_color":"#1976D2","sql_expression":"sum(a.qty*d.valuation_rate*a.conversion_factor)"},
			{"label":"Tax and Charge", "short_label":"Comm.", "fieldname":"tax_and_charge","fieldtype":"Currency","indicator":"Green","precision":None, "align":"right","chart_color":"#FF3D00","sql_expression":"sum(coalesce(a.item_tax,0))"},		
			{"label":"Amount", "short_label":"Amt", "fieldname":"amount","fieldtype":"Currency","indicator":"Red","precision":None, "align":"right","chart_color":"#2E7D32","sql_expression":"sum(a.net_amount)"},
			{"label":"Profit", "short_label":"Prof.", "fieldname":"profit","fieldtype":"Currency","indicator":"Green","precision":None, "align":"right","chart_color":"#FF3D00","sql_expression":"sum(a.net_amount + coalesce(a.item_tax,0) - (a.qty*d.valuation_rate*a.conversion_factor))"}
		]
	elif(filters.parent_row_group is None and filters.row_group == "Product"):
		return [
			{"label":"Transaction","short_label":"Tran.", "fieldname":"transaction","fieldtype":"Float", "indicator":"Grey","precision":2, "align":"center","chart_color":"#f030fd","sql_expression":"coalesce(c.transaction,0)"},
			{"label":"Quantity","short_label":"Qty", "fieldname":"qty","fieldtype":"Float","indicator":"Grey","precision":2, "align":"center","chart_color":"#FF8A65","sql_expression":"sum(a.qty*a.conversion_factor)"},
			{"label":"Sub Total", "short_label":"Sub To.", "fieldname":"sub_total","fieldtype":"Currency","indicator":"Grey","precision":None, "align":"right","chart_color":"#dd5574","sql_expression":"sum(a.base_price_list_rate * a.qty)"},
			{"label":"Discount", "short_label":"Disc.", "fieldname":"discount_amount","fieldtype":"Currency","indicator":"Grey","precision":None, "align":"right","chart_color":"#dd5574","sql_expression":"sum(a.base_price_list_rate*a.qty-a.net_amount)"},
			{"label":"Cost","short_label":"Cost", "fieldname":"cost","fieldtype":"Currency","indicator":"Blue","precision":None, "align":"right","chart_color":"#1976D2","sql_expression":"sum(a.qty*d.valuation_rate*a.conversion_factor)"},
			{"label":"Tax and Charge", "short_label":"Comm.", "fieldname":"tax_and_charge","fieldtype":"Currency","indicator":"Green","precision":None, "align":"right","chart_color":"#FF3D00","sql_expression":"sum(coalesce(a.item_tax,0))"},		
			{"label":"Amount", "short_label":"Amt", "fieldname":"amount","fieldtype":"Currency","indicator":"Red","precision":None, "align":"right","chart_color":"#2E7D32","sql_expression":"sum(a.net_amount)"},
			{"label":"Profit", "short_label":"Prof.", "fieldname":"profit","fieldtype":"Currency","indicator":"Green","precision":None, "align":"right","chart_color":"#FF3D00","sql_expression":"sum(a.net_amount + coalesce(a.item_tax,0) - (a.qty*d.valuation_rate*a.conversion_factor))"}
		]
	else:
		return [
			{"label":"Transaction","short_label":"Tran.", "fieldname":"transaction","fieldtype":"Float", "indicator":"Grey","precision":2, "align":"center","chart_color":"#f030fd","sql_expression":"sum(a.total_transaction)"},
			{"label":"Quantity","short_label":"Qty", "fieldname":"qty","fieldtype":"Float","indicator":"Grey","precision":2, "align":"center","chart_color":"#FF8A65","sql_expression":"sum(a.qty*a.conversion_factor)"},
			{"label":"Sub Total", "short_label":"Sub To.", "fieldname":"sub_total","fieldtype":"Currency","indicator":"Grey","precision":None, "align":"right","chart_color":"#dd5574","sql_expression":"sum(a.base_price_list_rate * a.qty)"},
			{"label":"Discount", "short_label":"Disc.", "fieldname":"discount_amount","fieldtype":"Currency","indicator":"Grey","precision":None, "align":"right","chart_color":"#dd5574","sql_expression":"sum(a.base_price_list_rate*a.qty-a.net_amount)"},
			{"label":"Cost","short_label":"Cost", "fieldname":"cost","fieldtype":"Currency","indicator":"Blue","precision":None, "align":"right","chart_color":"#1976D2","sql_expression":"sum(a.qty*d.valuation_rate*a.conversion_factor)"},
			{"label":"Tax and Charge", "short_label":"Comm.", "fieldname":"tax_and_charge","fieldtype":"Currency","indicator":"Green","precision":None, "align":"right","chart_color":"#FF3D00","sql_expression":"sum(coalesce(a.item_tax,0))"},		
			{"label":"Amount", "short_label":"Amt", "fieldname":"amount","fieldtype":"Currency","indicator":"Red","precision":None, "align":"right","chart_color":"#2E7D32","sql_expression":"sum(a.net_amount)"},
			{"label":"Profit", "short_label":"Prof.", "fieldname":"profit","fieldtype":"Currency","indicator":"Green","precision":None, "align":"right","chart_color":"#FF3D00","sql_expression":"sum(a.net_amount + coalesce(a.item_tax,0) - (a.qty*d.valuation_rate*a.conversion_factor))"}
		]

def get_row_groups():
	return [
		{
			"fieldname":"a.parent",
			"label":"Sale Invoice",
			"parent_row_group_filter_field":"row_group"
		},
		{
			"fieldname":"a.item_group",
			"label":"Category",
			"parent_row_group_filter_field":"row_group"
		},
		{
			"fieldname":"a.parent_item_group",
			"label":"Product Group",
			"parent_row_group_filter_field":"row_group"
		},
		{
			"fieldname":"b.company",
			"label":"Company",
			"parent_row_group_filter_field":"row_group"
		},
		{
			"fieldname":"ifnull(b.branch,'Not Set')",
			"label":"Branch",
			"parent_row_group_filter_field":"row_group"
		},
		{
			"fieldname":"ifnull(b.pos_profile,'Not Set')",
			"label":"POS Profile",
			"parent_row_group_filter_field":"row_group"
		},
		{
			"fieldname":"b.customer_name",
			"label":"Customer",
			"parent_row_group_filter_field":"row_group"
		},
		{
			"fieldname":"b.customer_group",
			"label":"Customer Group",
			"parent_row_group_filter_field":"row_group"
		},
		{
			"fieldname":"ifnull(b.Territory,'Not Set')",
			"label":"Territory",
			"parent_row_group_filter_field":"row_group"
		},
		
		{
			"fieldname":"ifnull(b.set_warehouse,'Not Set')",
			"label":"Warehouse",
			"parent_row_group_filter_field":"row_group"
		},
		{
			"fieldname":"date_format(b.posting_date,'%%Y/%%m/%%d')",
			"label":"Date",
			"parent_row_group_filter_field":"row_group"
		},
		{
			"fieldname":"date_format(b.posting_date,'%%Y/%%m')",
			"label":"Month",
			"parent_row_group_filter_field":"row_group"
		},
		{
			"fieldname":"date_format(b.posting_date,'%%Y')",
			"label":"Year",
			"parent_row_group_filter_field":"row_group"
		},
		{
			"fieldname":"ifnull(a.brand,'Not Set')",
			"label":"Brand",
			"parent_row_group_filter_field":"row_group"
		},
		{
			"fieldname":"ifnull(b.membership,'Not Set')",
			"label":"Membership",
			"parent_row_group_filter_field":"row_group"
		},
		{
			"fieldname":"a.item_name",
			"label":"Product"
		},
		{
			"fieldname":"ifnull(a.supplier_name,'Not Set')",
			"label":"Supplier",
			"parent_row_group_filter_field":"row_group"
		},
		{
			"fieldname":"ifnull(a.supplier_group,'Not Set')",
			"label":"Supplier Group",
			"parent_row_group_filter_field":"row_group"
		},
		{
			"fieldname":"b.selling_price_list",
			"label":"Sale Type",
			"parent_row_group_filter_field":"row_group"
		},
	]