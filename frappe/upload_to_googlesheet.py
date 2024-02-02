import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials
from frappe.desk.query_report import run
import frappe
@frappe.whitelist()
def upload_to_google_sheet(start_date,end_date):
    
    settings = frappe.get_doc('System Settings')
    response = run("Sale Product Summary By Month",filters={"start_date": start_date, "end_date": end_date})
    result = response.get("result")
    columns = response.get("columns")

    creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(settings.google_account_credentials))
    client = gspread.authorize(creds)
    sheet = client.open('la_sale_data').sheet1
    if len(sheet.get("1:1")[0]) <= 0:
        sheet.append_rows([[obj.label for obj in columns]])
    report_data = convert_to_nested_arrays(result,columns)
    resp = sheet.append_rows(report_data) 
    frappe.msgprint("Export Successfully")
    return resp

def convert_to_nested_arrays(json_data,columns):
    if(len(json_data) > 0):
        keys = [{"fieldname": item["fieldname"], "fieldtype": item["fieldtype"]} for item in columns]
        result = [[ entry[key['fieldname']] for key in keys] for entry in json_data]
        return result
    else:
         return []