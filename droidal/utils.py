import frappe
from frappe import _
from frappe.auth import LoginManager
import calendar
from datetime import date
from frappe import _
import json
import requests
from datetime import datetime, date, timedelta

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
     
     
    
    
@frappe.whitelist()
def test():
    document = frappe.get_doc("Employee","DRD-1209")    
    return document
    
    


@frappe.whitelist()
def check_login(username, password):
    try:
        # Get actual user ID
        user_id = frappe.get_value("User", username, "name") or username

        # Check password directly
        from frappe.utils.password import check_password
        check_password(user_id, password)

        # Perform login
        login_manager = LoginManager()
        login_manager.authenticate(user_id, password)
        login_manager.post_login()

        return {
            "status": "success",
            "message": _("Login successful"),
            "user": user_id
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



@frappe.whitelist()
def get_sal_structure(sal_structure):
    try:
        # Query to fetch documents from child table
        results = frappe.db.sql("""
            SELECT *
            FROM `tabSalary Detail`
            WHERE parent = %s
        """, (sal_structure,), as_dict=True)


        earnings = []
        deductions = []

        for row in results:
            if row.get("parentfield") == "earnings":
                earnings.append(row)
            if row.get("parentfield") == "deductions":
                deductions.append(row)

        if earnings or deductions:
            return {"status": "success", "earnings": earnings, "deductions": deductions}
        else:
            return {"status": "not_found", "message": "No salary structure found."}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_sal_structure API")
        return {"status": "error", "message": str(e)}


from datetime import datetime, timedelta
import frappe
from frappe.utils import now_datetime

@frappe.whitelist()
def get_punch_status():
    employee = frappe.session.user

    # Fetch shift timings for today
    shift = frappe.db.sql("""
        SELECT s.start_time, s.end_time
        FROM `tabEmployee` sa
        JOIN `tabShift Type` s ON sa.default_shift = s.name
        WHERE sa.user_id = %s
        LIMIT 1
    """, (employee,), as_dict=True)

    if shift:
        start_time = (datetime.min + shift[0].start_time).time() if isinstance(shift[0].start_time, timedelta) else shift[0].start_time
        end_time = (datetime.min + shift[0].end_time).time() if isinstance(shift[0].end_time, timedelta) else shift[0].end_time
    else:
        start_time = end_time = None

    employee = frappe.db.get_value("Employee", {"user_id": employee}, "name")
    last_punch = frappe.db.sql("""
        SELECT log_type, time
        FROM `tabEmployee Checkin`
        WHERE employee = %s
        ORDER BY time DESC
        LIMIT 1
    """, (employee,), as_dict=True)

    now_time = now_datetime()

    def is_within_shift():
        """Check if the current time is within the shift timings, including overnight shifts."""
        if not start_time or not end_time:
            return False

        now_t = now_time.time()

        if start_time <= end_time:
            # Normal same-day shift
            return start_time <= now_t <= end_time
        else:
            # Overnight shift: passes midnight
            return now_t >= start_time or now_t <= end_time

    within_shift = is_within_shift()

    if last_punch and last_punch[0].log_type == "IN":
        return {
            "status": "in",
            "start_time": last_punch[0].time,
            "within_shift": within_shift,
            "shift_start": start_time,
            "shift_end": end_time,
            "server_now": now_time   # ⬅️ Important
        }
    return {
        "status": "out",
        "within_shift": within_shift,
        "shift_start": start_time,
        "shift_end": end_time,
        "server_now": now_time       # ⬅️ Important
    }


@frappe.whitelist()
def punch_in():
    """Create a new Employee Checkin record for IN punch"""
    employee = frappe.session.user
    employee = frappe.db.get_value("Employee", {"user_id": employee}, "name")
    now_time = now_datetime()
    doc = frappe.get_doc({
        "doctype": "Employee Checkin",
        "employee": employee,
        "time": now_time,
        "log_type": "IN"
    })
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    return {
        "status": "success",
        "start_time": doc.time,
        "server_now": now_time    # ⬅️ Important
    }


@frappe.whitelist()
def punch_out():
    """Create a new Employee Checkin record for OUT punch"""
    employee = frappe.session.user
    employee = frappe.db.get_value("Employee", {"user_id": employee}, "name")
    now_time = now_datetime()
    doc = frappe.get_doc({
        "doctype": "Employee Checkin",
        "employee": employee,
        "time": now_time,
        "log_type": "OUT"
    })
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    return {
        "status": "success",
        "server_now": now_time     # ⬅️ Important
    }



@frappe.whitelist()
def replace_salary_structure(salary_structure, employee):
    employee_doc = frappe.get_doc("Employee", employee)

    # 🔎 Look for "Basic" in Employee's custom earnings child table
    ctc = employee_doc.ctc or 0

    # 📝 Create Salary Structure Assignment
    assignment = frappe.get_doc({
        "doctype": "Salary Structure Assignment",
        "employee": employee,
        "salary_structure": salary_structure,
        "from_date": frappe.utils.nowdate(),
        "base": ((ctc/12)/2) or 0,
    })
    assignment.insert(ignore_permissions=True)
    frappe.db.commit()
    return assignment.name


@frappe.whitelist()
def employee_get_all_salay_amount(ctc, employee):
    # Basic\
    ctc = float(ctc)
    fixed = ctc

    basic = (ctc / 2)/12

    basic = round(basic, 2)
    
    # HRA
    hra = (basic / 2)

    hra = round(hra, 2)
    
    # Mobile Allowance
    if 300000 < ctc <= 1200000:
        mobile_allowance = 12000
    elif ctc <= 300000:
        mobile_allowance = 6000
    else:
        mobile_allowance = 30000

    mobile_allowance = (mobile_allowance / 12)
    
    mobile_allowance = round(mobile_allowance, 2)


    check_basic = basic*12
    if check_basic < 180000:
        pf_employer = (check_basic * (12/100))/12
    else:
        pf_employer = (21600/12)
        


    pf_employer = round(pf_employer, 2)

    gratuity = basic*(4.81/100)

    gratuity = round(gratuity, 2)

    pf_employee = pf_employer

    children_allowance = 500






    employee_doc = frappe.get_doc("Employee", employee)

    age = employee_doc.custom_age
    if age is None:
        frappe.throw(_("Please set the age of the employee."))

    # get all ages from Age doctype and convert to integers
    age_list = frappe.get_all("Health Insurance", fields=["name"])
    ages = sorted([int(a["name"]) for a in age_list])

    # find the largest age that is <= employee's age
    lower_age = max([a for a in ages if a <= int(age)], default=None)

    next_age = min([a for a in ages if a > lower_age], default=None) if lower_age is not None else None

    medical_insurance = frappe.get_value("Health Insurance", {"name": next_age}, "employer")

    medical_insurance = medical_insurance or 0

    medical_insurance = round((medical_insurance / 12), 2)



    if 1200000 < ctc <= 2400000:
        lta = 62400
    elif 2400000 < ctc <= 3600000:
        lta = 120000
    elif ctc > 3600000:
        lta = 360000
    else:
        lta = 0
    lta = round((lta / 12),2)


    if ctc> 360000:
        conveyance_allowance = 19200
    else:
        conveyance_allowance = 0
    conveyance_allowance = round((conveyance_allowance / 12),2)

    if ctc > 1200000:
        fuel_and_maintenance = 21600
    else:
        fuel_and_maintenance = 0
    fuel_and_maintenance = round((fuel_and_maintenance / 12),2)


    if ctc > 1200000:
        driver_reimbursement = 10800
    else:
        driver_reimbursement = 0
    driver_reimbursement = round((driver_reimbursement / 12),2)

    if ctc > 2400000:
        books_and_periodicals = 24000
    else:
        books_and_periodicals = 0
    books_and_periodicals  = round((books_and_periodicals / 12),2)


    total_earnings = fixed -(pf_employer+gratuity+medical_insurance)

    if total_earnings > 252000:
        esi_employer = 0
    else:
        esi_employer = total_earnings * (3.25 / 100)
    
    esi_employer = round(esi_employer, 2)

    if total_earnings > 252000:
        esi_employee = 0
    else:
        esi_employee = total_earnings * (0.75 / 100)
    
    esi_employee = round(esi_employee, 2)


    
    special_allowance = max((ctc/12) - (basic + hra + children_allowance + mobile_allowance+conveyance_allowance+ fuel_and_maintenance + driver_reimbursement + books_and_periodicals + lta+
                               medical_insurance + pf_employer + gratuity +esi_employer), 0)
    
    
    special_allowance = round(special_allowance, 2)


        # Define mappings for earnings and deductions
    earning_map = {
        "Basic Component": basic,
        "HRA Component": hra,
        "Mobile Allowance": mobile_allowance,
        "Children Education Allowance": children_allowance,
        "Special Allowance": special_allowance,
        "LTA": lta,
        "Conveyance Allowance": conveyance_allowance,
        "Fuel & Maintenance": fuel_and_maintenance,
        "Driver Reimbursment": driver_reimbursement,
        "Books & Periodicals": books_and_periodicals
    }

    deduction_map = {
        "PF Payer Component": pf_employer,
        "PF Payee Component": pf_employee,
        "Gratuity": gratuity,
        "Medical Insurance Component": medical_insurance,
        "ESI Payer": esi_employer,
        "ESI Payee": esi_employee
    }

    # Clear and re-add earnings rows
    if hasattr(employee_doc, "custom_earnings"):
        employee_doc.custom_earnings = []  # Clear existing rows
        for component, amount in earning_map.items():
            employee_doc.append("custom_earnings", {
                "salary_component": component,
                "amount": amount,
                "additional_salary": ""
            })

    # Clear and re-add deduction rows
    if hasattr(employee_doc, "custom_deductions"):
        employee_doc.custom_deductions = []  # Clear existing rows
        for component, amount in deduction_map.items():
            employee_doc.append("custom_deductions", {
                "salary_component": component,
                "amount": amount,
                "additional_salary": ""
            })


    employee_doc.save(ignore_permissions=True)
    frappe.db.commit()
    employee_doc.reload()



@frappe.whitelist()
def get_employee_attendance():
    user_id = frappe.session.user
    employee_id = frappe.db.get_value("Employee", {"user_id": user_id}, "name")
    
    if not employee_id:
        employee_id = "DRD-1169"  # Default to Karthik
    
    try:
        records = frappe.get_all(
            "Attendance",
            filters={"employee": employee_id},
            fields=["employee", "employee_name", "attendance_date", "status"],
            order_by="attendance_date asc"
        )
        
        # Convert to a dictionary for easier lookup
        attendance_dict = {}
        for record in records:
            date_key = record.attendance_date.strftime("%Y-%m-%d")
            attendance_dict[date_key] = record.status
        
        # Just show a simple summary
        frappe.msgprint(f"Loaded attendance for {len(records)} dates")
        
        return attendance_dict
        
    except Exception as e:
        frappe.msgprint(f"Error: {str(e)}")
        return {}
    


@frappe.whitelist()
def get_professional_tax(name):
    salary_slip_doc = frappe.get_doc("Salary Slip", name)
    gross_salary = salary_slip_doc.gross_pay
    try:
        professional_tax = frappe.get_all(
            "Professional Tax",
            filters={"basic_range_from":["<=", gross_salary],
                    "basic_range_to":[">=", gross_salary],
                    "from_date":["<=", salary_slip_doc.start_date],
                    },
            fields=["tax_amount"],
            order_by="from_date desc",
            limit_page_length=1
        )

        if professional_tax:
            salary_detail_exists = frappe.db.exists({
                "doctype": "Salary Detail",
                "parent": name,
                "salary_component": "Professional Tax"
            })
            if salary_detail_exists:
                return {"status": "exists", "message": "Professional Tax already exists in Salary Slip."}



            salary_detail = frappe.new_doc("Salary Detail")
            salary_detail.salary_component = "Professional Tax"
            salary_detail.amount = professional_tax[0].tax_amount
            salary_detail.parent = name
            salary_detail.parentfield = "deductions"
            salary_detail.parenttype = "Salary Slip"
            salary_detail.save(ignore_permissions=True)
            frappe.db.commit()        

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_professional_tax API")
        return {"status": "error", "message": str(e)}
    


@frappe.whitelist()


def mark_attendance_based_on_hours(from_date=None):
    # If no date is given, default to today
    if not from_date:
        from_date = date.today()-timedelta(days=1)

    get_employee = frappe.get_all(
        "Employee",
        filters={"status": "Active"},
        fields=["name"]
    )

    for emp in get_employee:
        employee = emp.name

        # Get all check-ins after given date
        checkins = frappe.get_all(
            "Employee Checkin",
            filters={
                "employee": employee,
                "time": [">=", from_date]  # Only logs after this date
            },
            fields=["time", "log_type"],
            order_by="time asc"
        )

        if not checkins:
            continue

        i = 0
        while i < len(checkins):
            if checkins[i].log_type == "IN":
                check_in_time = checkins[i].time
                check_in_date = check_in_time.date()
                if check_in_date == date.today():
                    i += 1
                    continue

                # Find next OUT after this IN
                next_out = None
                for j in range(i + 1, len(checkins)):
                    if checkins[j].log_type == "OUT":
                        next_out = checkins[j].time
                        i = j  # Move pointer to OUT index for next iteration
                        break

                if next_out:
                    worked_hours = (next_out - check_in_time).total_seconds() / 3600

                    if worked_hours >= 8:
                        existing = frappe.get_all(
                            "Attendance",
                            filters={"employee": employee, "attendance_date": check_in_date},
                            limit_page_length=1
                        )

                        if not existing:
                            att_doc = frappe.get_doc({
                                "doctype": "Attendance",
                                "employee": employee,
                                "attendance_date": check_in_date,
                                "status": "Present"
                            })
                            att_doc.insert(ignore_permissions=True)
                            frappe.db.commit()

            i += 1
