# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
	return get_columns(filters),get_report_data(filters)


def get_columns(filters):
	columns = []
	columns.append({'fieldname':'mode_of_payment','label':"Payment Type",'fieldtype':'Data','align':'center','width':150})
	columns.append({'fieldname':'payment_amount','label':"Payment Amount",'fieldtype':'Currency','align':'right','width':150})
	# columns.append({'fieldname':'closing_amount','label':"Actual Amount",'fieldtype':'Currency','align':'right','width':150})
	# columns.append({'fieldname':'different_amount','label':"Different",'fieldtype':'Currency','align':'right','width':150})
	return columns

def get_report_data(filters):
	sql = """
				WITH pos_opening_entry_id AS( 
				SELECT 
				pos_opening_entry_id 
				FROM `tabPOS Closing Entry` 
				WHERE posting_date between '{0}' and '{1}' and 
				company = '{2}')

				, change_amount AS(
				SELECT 
				'Cash' mode_of_payment,
				sum(change_amount) change_amount
				FROM `tabPOS Invoice` 
				WHERE pos_opening_entry_id IN (SELECT * FROM pos_opening_entry_id) AND docstatus=1
				and branch = case when '{3}' = 'None' then branch else '{3}' end)

				, set_cash AS(SELECT 'Cash' AS mode_of_payment,0 AS total_amount)

				, paid_amount AS(
				SELECT 
				mode_of_payment,
				sum(amount) total_amount
				FROM `tabSales Invoice Payment` a
				INNER JOIN `tabPOS Invoice` b ON b.name = a.parent
				WHERE b.pos_opening_entry_id IN (SELECT * FROM pos_opening_entry_id) AND b.docstatus=1
				and branch = case when '{3}' = 'None' then branch else '{3}' end
				GROUP BY a.mode_of_payment)

				, payment AS(
				SELECT mode_of_payment,SUM(total_amount) total_amount FROM(
				SELECT * FROM set_cash
				UNION all
				SELECT * FROM paid_amount) a
				GROUP BY mode_of_payment)

				SELECT 
				a.mode_of_payment,
				total_amount - coalesce(change_amount,0) payment_amount
				FROM payment a
				LEFT JOIN change_amount b ON b.mode_of_payment = a.mode_of_payment
				""".format(filters.start_date,filters.end_date,filters.company,filters.branch)
	frappe.msgprint(sql)
	data = frappe.db.sql(sql,as_dict=1)
	return data
