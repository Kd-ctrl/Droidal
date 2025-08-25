import frappe
from frappe.utils import get_url
from frappe.utils.pdf import get_pdf

from frappe.utils.print_format import download_pdf
import time


@frappe.whitelist()
def download_salary_slip(month, year):
    month = int(month)
    year = int(year)

    employee = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
    if not employee:
        frappe.throw("No Employee record found for the logged-in user.")

    slip = frappe.db.sql("""
        SELECT name FROM `tabSalary Slip`
        WHERE MONTH(start_date) = %s
          AND YEAR(start_date) = %s
          AND employee = %s
        LIMIT 1
    """, (month, year, employee), as_dict=True)

    if not slip:
        frappe.throw("No salary slip found for the selected month and year.")

    slip_name = slip[0].name
    uri = f"https://nila.droidal.com/printview?doctype=Salary%20Slip&name={slip_name}&trigger_print=1&format=sal%20slip%20test&no_letterhead=1&letterhead=No%20Letterhead&settings=%7B%7D&_lang=en"

    return {"pdf_url": uri}
    
    
    
    
    
    
def auto_assign_employee(doc, method):
    if doc.employee:
        # Get the user_id of the employee
        user_id = frappe.db.get_value("Employee", doc.employee, "user_id")
        if user_id:
          already_shared = frappe.db.exists("DocShare", {
              "share_doctype": "Salary Slip",
              "share_name": doc.name,
              "user": user_id
          })
          if already_shared:
              return True
  
          frappe.share.add("Salary Slip", doc.name, user_id, read=1, write=0)
          frappe.db.commit()
          return True



@frappe.whitelist()
def share_docs_with_employees(doctype_name):
    docs = frappe.get_all(doctype_name, fields=["name", "employee"])
    shared_count = 0

    for doc in docs:
        if not doc.employee:
            continue

        user_id = frappe.db.get_value("Employee", doc.employee, "user_id")
        if not user_id:
            continue

        # Avoid duplicate shares
        already_shared = frappe.db.exists("DocShare", {
            "share_doctype": doctype_name,
            "share_name": doc.name,
            "user": user_id
        })
        if already_shared:
            continue

        frappe.share.add(doctype_name, doc.name, user_id, read=1, write=0)
        shared_count += 1
        
    frappe.db.commit()

    return f"? Shared {shared_count} documents with linked employees."








