# Copyright (c) 2023, ratha and contributors
# For license information, please see license.txt

import ftplib, frappe
import os, shutil
import shlex, subprocess
import time
from frappe.model.document import Document
from frappe.utils import cstr

@frappe.whitelist()
def execute_backup_command():
    site_name = cstr(frappe.local.site)
    folder = '/home/erpuser/pro-bench/sites/' + site_name + '/private/backups'
    setting = frappe.get_doc('System Settings')
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

    run_bench_command("bench --site " + site_name + " backup --with-files")

    time.sleep(2)

    session = ftplib.FTP_TLS(setting.ftp_url,setting.ftp_user,setting.ftp_password)
    if site_name in session.nlst():
        session.cwd(site_name)
    else : 
        session.mkd(site_name)
        session.cwd(site_name)
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        file = open(file_path,'rb')
        session.storbinary('STOR ' + filename, file)
        file.close()
    session.quit()
    return "Done"

def run_bench_command(command, kwargs=None):
    site = {"site": frappe.local.site}
    cmd_input = None
    if kwargs:
        cmd_input = kwargs.get("cmd_input", None)
        if cmd_input:
            if not isinstance(cmd_input, bytes):
                raise Exception(f"The input should be of type bytes, not {type(cmd_input).__name__}")
            del kwargs["cmd_input"]
        kwargs.update(site)
    else:
        kwargs = site
    command = " ".join(command.split()).format(**kwargs)
    command = shlex.split(command)
    subprocess.run(command, input=cmd_input, capture_output=True)