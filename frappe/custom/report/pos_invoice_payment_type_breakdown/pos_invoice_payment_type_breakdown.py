# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
	data = get_raw_data(filters)
	return get_columns(filters,data),get_report_data(filters,data)


def get_columns(filters,data):
	columns = []
	columns.append({'fieldname':'posting_date','label':"Date",'fieldtype':'Date','align':'center','width':150})
	payment_types =set( [d["mode_of_payment"] for d in data])
	for pt in payment_types:
		columns.append({'fieldname':pt.lower().replace(" ","_"),'label':pt,'fieldtype':'Float','align':'center','width':150})
	columns.append({'fieldname':'total_payment','label':"Total Payment",'fieldtype':'Currency','align':'right','width':150})
	return columns

def get_report_data(filters,data):
	payment_types = set( [d["mode_of_payment"].lower().replace(" ","_") for d in data])
	dates = set( [d["posting_date"] for d in data])
	report_data = []
	for d in dates:
		record = {"posting_date":d}
		for pt in payment_types:
			pt_data = [x for x in data if x["posting_date"] ==d and x["mode_of_payment"].lower().replace(" ","_") == pt]
			if len(pt_data)>0:
				record[pt] = pt_data[0]["payment_amount"] or 0
			else:
				record[pt] = 0
		record["total_payment"] = pt_data = sum([(x["payment_amount"] or 0) for x in data if x["posting_date"] ==d])
		report_data.append(record)
	return report_data

def get_raw_data(filters):
	sql = """
				WITH pos_opening_entry_id AS( 
				SELECT 
				pos_opening_entry_id 
				FROM `tabPOS Closing Entry` 
				WHERE posting_date between '{0}' and '{1}' and 
				company = '{2}')

				, change_amount AS(
				SELECT 
				posting_date,
				'Cash' mode_of_payment,
				sum(change_amount) change_amount
				FROM `tabPOS Invoice` 
				WHERE pos_opening_entry_id IN (SELECT * FROM pos_opening_entry_id) AND docstatus=1
				and coalesce(branch,'None') = case when '{3}' = 'None' then coalesce(branch,'None') else '{3}' end AND consolidated_invoice IS not null 
				GROUP BY posting_date)

				, set_cash AS(
				SELECT 
				posting_date,
				'Cash' mode_of_payment,
			    0 change_amount
				FROM `tabPOS Invoice` 
				WHERE pos_opening_entry_id IN (SELECT * FROM pos_opening_entry_id) AND docstatus=1
				AND consolidated_invoice IS not NULL GROUP BY posting_date)

				, paid_amount AS(
				SELECT 
				posting_date,
				mode_of_payment,
				sum(amount) total_amount
				FROM `tabSales Invoice Payment` a
				INNER JOIN `tabPOS Invoice` b ON b.name = a.parent
				WHERE b.pos_opening_entry_id IN (SELECT * FROM pos_opening_entry_id) AND b.docstatus=1
				and coalesce(branch,'None') = case when '{3}' = 'None' then coalesce(branch,'None') else '{3}' end AND b.consolidated_invoice IS not null
				GROUP BY posting_date,a.mode_of_payment)
				
				, payment_entry AS(
				SELECT 
				a.posting_date,
				c.mode_of_payment,
				SUM(allocated_amount) total_amount
				FROM `tabSales Invoice` a
				INNER JOIN `tabPayment Entry Reference` b ON b.reference_name = a.name
				INNER JOIN `tabPayment Entry` c ON c.name = b.parent
				WHERE a.posting_date BETWEEN '{0}' and '{1}' and a.company = '{2}' and c.docstatus=1
				and coalesce(a.branch,'None') = case when '{3}' = 'None' then coalesce(a.branch,'None') else '{3}' end
				GROUP BY a.posting_date,c.mode_of_payment
				)

				,sale_invoice as(
				SELECT
				b.posting_date,
				a.mode_of_payment,
				SUM(amount) total_amount
				FROM `tabSales Invoice Payment` a
				INNER JOIN `tabSales Invoice` b ON b.name = a.parent
				WHERE b.posting_date BETWEEN '{0}' and '{1}' and b.company = '{2}' AND id IS null
				and coalesce(b.branch,'None')= case when '{3}' = 'None' then coalesce(b.branch,'None') else '{3}' end
				AND parenttype='Sales Invoice' AND b.status='Paid' AND b.docstatus=1 AND b.is_consolidated=0
				GROUP BY b.posting_date,a.mode_of_payment
				)

				, payment AS(
				SELECT posting_date,mode_of_payment,SUM(total_amount) total_amount FROM(
				select * from sale_invoice
				union all
				SELECT * FROM payment_entry
				UNION all
				SELECT * FROM set_cash
				UNION all
				SELECT * FROM paid_amount) a
				GROUP BY posting_date,mode_of_payment)

				SELECT 
				a.posting_date,
				a.mode_of_payment,
				cast(total_amount - coalesce(change_amount,0) as decimal(16,4)) payment_amount
				FROM payment a
				LEFT JOIN change_amount b ON b.mode_of_payment = a.mode_of_payment AND b.posting_date = a.posting_date
				where a.mode_of_payment is not null
				order by a.posting_date
				""".format(filters.start_date,filters.end_date,filters.company,filters.branch)
	data = frappe.db.sql(sql,as_dict=1)
	return data
