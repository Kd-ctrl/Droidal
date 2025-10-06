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
    
    


# droidal/utils.py
import frappe
from frappe import _
from datetime import datetime, date
import requests
from requests.auth import HTTPBasicAuth
import json
@frappe.whitelist()
def webhook_for_employee(doc, method=None):
    if getattr(frappe.flags, "in_webhook_for_employee", False):
        return
    frappe.flags.in_webhook_for_employee = True
    try:
        def convert_dates(obj):
            if isinstance(obj, (datetime, date)):
                return obj.isoformat()
            if isinstance(obj, dict):
                return {k: convert_dates(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [convert_dates(i) for i in obj]
            return obj

        document_dict = convert_dates(doc.as_dict())
        url = "http://cxo.droidal.com/api/nila_users_webhook/"
        payload = {"document": document_dict}
        headers = {"Content-Type": "application/json"}

        try:
            resp = requests.post(
                url,
                data=json.dumps(payload),
                headers=headers,
                auth=HTTPBasicAuth("lar3fb7pi4z6dhk", "uhest1p6zf8qgdi"),
                timeout=10,
            )
            resp.raise_for_status()
        except requests.RequestException as e:
            frappe.log_error(f"Webhook call failed for {doc.name}: {e}", "webhook_for_employee")
    finally:
        frappe.flags.in_webhook_for_employee = False
    
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
            "server_now": now_time   
        }
    return {
        "status": "out",
        "within_shift": within_shift,
        "shift_start": start_time,
        "shift_end": end_time,
        "server_now": now_time      
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
def replace_salary_structure(doc, method=None):
    # --- guard to prevent infinite loop ---
    if getattr(frappe.flags, "in_replace_salary_structure", False):
        return
    frappe.flags.in_replace_salary_structure = True

    try:
        ctc = doc.ctc or 0
        today = frappe.utils.nowdate()

        # existing = frappe.get_all(
        #     "Salary Structure Assignment",
        #     filters={
        #         "employee": doc.name,
        #         "salary_structure": doc.custom_salary_structure,
        #         "from_date": today,
        #         "status": "Submitted"
        #     },
        #     pluck="name",
        # )

        # if existing:
        #     assignment = frappe.get_doc("Salary Structure Assignment", existing[0])
        #     assignment.base = (ctc / 12) / 2
        #     assignment.save(ignore_permissions=True)
        # else:
        assignment = frappe.get_doc({
            "doctype": "Salary Structure Assignment",
            "employee": doc.name,
            "salary_structure": doc.custom_salary_structure,
            "from_date": today,
            "base": (ctc / 12) / 2 if ctc else 0,
            "income_tax_slab": "fy 2024-20205",
        })
        assignment.insert(ignore_permissions=True)

        frappe.db.commit()
        return assignment.name
    finally:
        frappe.flags.in_replace_salary_structure = False



@frappe.whitelist()
def employee_get_all_salay_amount(doc, method=None):

    def get_hra(basic):
        if basic < 280000:
            result = basic * 0.10
        else:
            result = basic * 0.25
        return round(result)
    
    
    # --- guard to prevent infinite loop ---
    if getattr(frappe.flags, "in_salary_amount_calc", False):
        return
    frappe.flags.in_salary_amount_calc = True

    try:
        ctc = float(doc.ctc or 0)
        employee = doc.name

        # === Basic and HRA ===
        basic = round((ctc * 0.50), 2)
        hra = get_hra(ctc)
        
        # === Medical Insurance ===
        age = doc.custom_age
        if age is None:
            frappe.throw(_("Please set the age of the employee."))

        age_list = frappe.get_all("Health Insurance", fields=["name"])
        ages = sorted([int(a["name"]) for a in age_list]) if age_list else []
        lower_age = max([a for a in ages if a <= int(age)], default=None)
        next_age = min([a for a in ages if a > lower_age], default=None) if lower_age is not None else None
        medical_insurance = frappe.get_value("Health Insurance", {"name": next_age}, "employer") or 0

        # === Other allowances ===
        def get_lta(ctc):
            if ctc >=1200001:
                return 120000
            else:
                return 0
            
        lta = round(get_lta(ctc))
        conveyance_allowance = round(ctc * 0.03)


        # ############################
        # if gross <= 21000:
        #     satuatory_bonus = round(basic * 0.0833, 0)
        # else:
        #     satuatory_bonus = round(basic * 0.04, 0)
        # #############################

        # # === Special Allowance ===
        # special_allowance = max((ctc) - (basic + hra  + conveyance_allowance +satuatory_bonus),0)
        # special_allowance = round(special_allowance, 2)
        # gross = basic+hra+special_allowance+conveyance_allowance+lta 

        satuatory_bonus = 0
        # initial estimates
        gross = basic + hra + conveyance_allowance + lta
        prev_gross = 0
        pf_employer = gratuity = esi_employer = 0

        while abs(gross/12 - prev_gross/12) > 0.01:  # iterate until stable
            prev_gross = gross

            hidden = (gross - hra)

            # recalculate PF, gratuity, ESI
            pf_employer = round(21600 if hidden > 180000 else hidden * 0.12, 0)
            gratuity = round(basic * 0.0481, 0)
            esi_employer = round(0 if gross > 252000 else gross * 0.0325, 0)
            esi_employee = round(0 if gross > 252000 else gross * 0.0075, 0)
            other_benifits = pf_employer + gratuity + esi_employer

            # statutory bonus depends on gross
            if gross/12 <= 21000:
                satuatory_bonus = round(basic * 0.0833, 0)
            else:
                satuatory_bonus = round(basic * 0.04, 0)

            # special allowance depends on statutory bonus and other benefits
            special_allowance = max(ctc - (basic + hra + conveyance_allowance + satuatory_bonus + lta + other_benifits), 0)
            special_allowance = round(special_allowance, 2)

            # recalculate gross
            gross = basic + hra + special_allowance + conveyance_allowance + lta +satuatory_bonus

        pf_employee = pf_employer

        # final GMC premium
        if esi_employee == 0:
            gmc_premium = medical_insurance
        else:
            gmc_premium = 0


        professional_tax = get_professional_tax(gross)

        
        if esi_employee==0 :
           gmc_premium = medical_insurance 
        else :
           gmc_premium = 0

        # === Update child tables ===
        def rounding(component):
            return round(component, 0)
        earning_map = {
            "Basic Component": rounding(basic/12),
            "HRA Component": rounding(hra/12),
            "Conveyance Allowance": rounding(conveyance_allowance/12),
            "Statutory Bonus": rounding(satuatory_bonus/12),
            "Special Allowance": rounding(special_allowance/12),
            "LTA":rounding(lta/12),
        }
        deduction_map = {
            "PF Payer Component": rounding(pf_employer/12),
            "ESI Payer": rounding(esi_employer/12),
            "Gratuity": rounding(gratuity/12),
            "PF Payee Component": rounding(pf_employee/12),
            "ESI Payee": rounding(esi_employee/12),
            "GMC PREMIUM - EMPLOYEE": rounding(gmc_premium/12),
            "Professional Tax": rounding(professional_tax/12),
        }

        # === Clear existing rows in DB and insert new rows ===
        frappe.db.delete("Salary Detail", {"parent": employee})

        frappe.db.set_value("Employee", employee, "custom_calculated_gross_amount", gross)

        for comp, amt in earning_map.items():
            frappe.get_doc({
                "doctype": "Salary Detail",
                "parent": employee,
                "parentfield": "custom_earnings",
                "parenttype": "Employee",
                "salary_component": comp,
                "amount": amt
            }).insert(ignore_permissions=True)

        for comp, amt in deduction_map.items():
            frappe.get_doc({
                "doctype": "Salary Detail",
                "parent": employee,
                "parentfield": "custom_deductions",
                "parenttype": "Employee",
                "salary_component": comp,
                "amount": amt
            }).insert(ignore_permissions=True)

        frappe.db.commit()

    finally:
        frappe.flags.in_salary_amount_calc = False


def get_deduction_amount(doc, method=None):
    exclude_list = ["Gratuity", "PF Payer Component","ESI Payer"]
    doc.custom_deduction = sum(
        d.amount for d in doc.deductions
        if d.salary_component not in exclude_list
    )
    doc.save(ignore_permissions=True)



@frappe.whitelist()
def get_employee_attendance():
    user_id = frappe.session.user
    employee_id = frappe.db.get_value("Employee", {"user_id": user_id}, "name")
    
    if not employee_id:
        frappe.msgprint("No employee detected")
    
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
        
        
        return attendance_dict
        
    except Exception as e:
        frappe.msgprint(f"Error: {str(e)}")
        return {}
    


def get_professional_tax(gross):
    value = (
    425 if gross <= 45000
    else 930 if gross <= 60000
    else 1025 if gross <= 75000
    else 1250
    )
    return value * 2

def get_night_shift_allowance(doc, method):
    nsa_list = frappe.get_all("NSA list", {},["name"])
    if doc.payment_days and nsa_list:
        nsa_list = [n['name'] for n in nsa_list]
        if doc.custom_holiday_ in nsa_list:
            get_attendance = frappe.get_all("Attendance", 
                                            filters={"employee":doc.employee,
                                            "attendance_date":["between",doc.start_date,doc.end_date],
                                            "status":"Work From Home",
                                            },
                                            fields=["status"]
                                            )
            work_from_home_days  = len(get_attendance)
            nsa_wfh = work_from_home_days*120
            work_from_office_days = abs(int(work_from_home_days) - int(doc.payment_days))
            nsa_wfo = work_from_office_days*170

            total = nsa_wfh + nsa_wfo

            week_off_allowance = frappe.db.get_all("Holiday Compensation", 
                                            filters={"employee":doc.employee,"date":["between",[doc.start_date,doc.end_date]]},
                                            fields=["*"])
            if week_off_allowance:
                total += (doc.gross_pay/doc.total_working_days )*len(week_off_allowance)
            
            frappe.get_doc({
                "doctype": "Salary Detail",
                "parent": doc.name,
                "parentfield": "earnings",
                "parenttype": "Salary Slip",
                "salary_component": "Other Earnings",
                "amount": int(total)
            }).insert(ignore_permissions=True)
            

            frappe.db.commit()
            


@frappe.whitelist()
def mark_attendance_based_on_hours(from_date=None):
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
