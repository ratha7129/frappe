import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials
from frappe.desk.query_report import run
import frappe
from  frappe.custom.report.sale_product_summary_by_month.sale_product_summary_by_month import get_data 
@frappe.whitelist()
def upload_to_google_sheet(start_date,end_date,branch="",pos_profile="",item_group="",item_category=""):
    settings = frappe.get_doc('System Settings')
    data = get_data(filters={
        "start_date": start_date, 
        "end_date": end_date,
        "branch": None if len(branch) <= 2 else branch.replace("\"","'").replace("[", "").replace("]","").replace("'","").split(','),
        "pos_profile": None if len(pos_profile) <= 2 else pos_profile.replace("\"","'").replace("[", "").replace("]","").replace("'","").split(','),
        "item_group": None if len(item_group) <= 2 else item_group.replace("\"","'").replace("[", "").replace("]","").replace("'","").split(','),
        "item_category": None if len(item_category) <= 2 else item_category.replace("\"","'").replace("[", "").replace("]","").replace("'","").split(',')
        })
    creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(settings.google_account_credentials))
    client = gspread.authorize(creds)
    sheet = client.open('la_sale_data').sheet1
    sheet.append_rows(data) 
    frappe.msgprint("Export Successfully")
 