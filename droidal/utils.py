import frappe
from frappe import _
from frappe.auth import LoginManager
import calendar
from datetime import date
from frappe import _
import json
import requests
from datetime import datetime, date

@frappe.whitelist()
def get_user_details():
    emp_details = frappe.get_list(
        "Employee",
        filters={"status":"Active"},
        fields=["employee", "first_name", "last_name", "user_id","employee_name", "designation","branch","employment_type"]
    )

    # Rename the keys in the output
    renamed_details = []
    for emp in emp_details:
        renamed_details.append({
            "employee_id": emp.get("employee"),
            "employee_firstname": emp.get("first_name"),
            "employee_lastname": emp.get("last_name"),
            "employee_email": emp.get("user_id"),
            "employee_username":emp.get("employee_name"),
            "designation":emp.get("designation"),
            "branch":emp.get("branch"),
            "employment_type":emp.get("employment_type")
        })

    return renamed_details
    
    


@frappe.whitelist()
def webhook_for_employee(name):

    document = frappe.get_doc("Employee",name)
    def convert_dates(obj):
        """Recursively convert datetime/date to ISO string format."""
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: convert_dates(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_dates(item) for item in obj]
        else:
            return obj


    document_dict = convert_dates(document.as_dict())
    
    
    
    dict_doc = document.as_dict()
    import requests
    from requests.auth import HTTPBasicAuth
        
    url = "http://cxo.droidal.com/api/nila_users_webhook/"
    
    payload = {
    "document":document_dict
    }
    
    headers = {
        "Content-Type": "application/json"
    }
        
    username = 'lar3fb7pi4z6dhk'
    password = 'uhest1p6zf8qgdi'
        
    import json
        
    response = requests.post(
        url,
        data=json.dumps(payload), 
        headers=headers,
        auth=HTTPBasicAuth(username, password)
    )
    print(response)
     
     
    
    
@frappe.whitelist()
def test():
    document = frappe.get_doc("Employee","DRD-1209")    
    return document
    
    


@frappe.whitelist()
def check_login(username, password):
    try:
        # Try to authenticate the user
        login_manager = LoginManager()
        login_manager.authenticate(username, password)
        login_manager.post_login()

        # If successful, return a success response
        return {
            "status": "success",
            "message": _("Login successful"),
            "user": username
        }

    except frappe.AuthenticationError:
        return {
            "status": "fail",
            "message": _("Invalid username or password")
        }




@frappe.whitelist()
def get_salary_slip(user_id, year, month):
    
    try:
        employee = frappe.db.get_value("Employee", {"user_id": user_id}, "name")
        year = int(year)
        month = int(month)
        last_day = calendar.monthrange(year, month)[1]

        start = date(year, month, 1)
        end = date(year, month, last_day)

        slips = frappe.get_all(
            "Salary Slip",
            filters={
                "employee": employee,
                "start_date": ["between", [start, end]],
            },
            fields=["*"],
            limit_page_length=1
        )

        if slips:
            return {"status": "success", "slip_name": slips}
        else:
            return {"status": "not_found", "message": "No salary slip found for this period."}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_salary_slip API")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def get_all_salary_slip():
    try:
        all_salary_slip = frappe.get_all("Salary Slip",filters={}, fields=["*"])

        if all_salary_slip:
            return {"status": "success", "slip_name": all_salary_slip}
    except Exception as e:
        return {"status":"error","message":str(e)}
