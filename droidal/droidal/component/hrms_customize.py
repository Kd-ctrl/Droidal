import frappe
from datetime import datetime , date, timedelta
from frappe.utils import getdate, date_diff, today


def last_day_of_month(any_day):
    next_month = any_day.replace(day=28) + timedelta(days=4)
    return next_month - timedelta(days=next_month.day)


@frappe.whitelist()
def get_available_leaves():
    employee , employee_id = get_cur_user_id()
    if not employee == "Administrator":
        leave_balances = {}
        leave_types = frappe.get_all('Leave Type', fields=['name'])
        this_year = datetime.today().strftime("%Y")
        this_month = datetime.today().strftime("%m")
        this_day = date.today()
        last_day = last_day_of_month(date(int(this_year), int(this_month), 1))
        total_leaves = 0
        
        for leave_type in leave_types:
            if leave_type['name'] != "Permission":
                allocations = frappe.get_all('Leave Allocation', filters={
                    'employee': employee_id[0],
                    'leave_type': leave_type['name'],
                    'to_date':[">", this_day]
                }, fields=['*'])
                print(allocations)
                if allocations:
                    
                    total_allocated = sum([(allocation['total_leaves_allocated'])/12 for allocation in allocations])
                    

                    leaves_taken = frappe.get_all('Leave Application', filters={
                        'employee': employee_id[0],
                        'leave_type': leave_type['name'],
                        'docstatus': 1  
                    }, fields=['from_date', 'to_date'])
                    total_taken = sum([
                        date_diff(getdate(leave['to_date']), getdate(leave['from_date'])) + 1
                        for leave in leaves_taken
                    ])
                    
                    available_leaves = int(total_allocated)- total_taken
                    total_leaves += available_leaves
        return total_leaves 
    else:
        return "NA"


def get_cur_user_id():
        employee = frappe.session.user
        if employee != "Administrator":
            employee_id = frappe.get_all("Employee",{"user_id":employee},pluck="name")
            if employee_id:
                return employee , employee_id
        else:
            return employee, None

@frappe.whitelist()
def get_all_permission_duration(from_date, to_date, from_time, to_time, employee):
    this_year = datetime.today().strftime("%Y")
    this_month = datetime.today().strftime("%m")
    this_day = date.today()
    last_day = last_day_of_month(date(int(this_year), int(this_month), 1))
    first_day = (date(int(this_year), int(this_month), 1))
    time_diff = timedelta()
    all_leave_application = frappe.get_all('Leave Application', filters={
                    'employee': employee,
                    'leave_type': "Permission",
                    'docstatus': 1, 
                    'from_date': ["between", [first_day,last_day]]
                }, fields=['*'])
    for leave_application in all_leave_application:

        initial_startdate = datetime.combine(leave_application["from_date"], datetime.min.time())

        startdatetime = initial_startdate + leave_application["from_time"]

        initial_enddate = datetime.combine(leave_application["to_date"], datetime.min.time())

        enddatetime = initial_enddate + leave_application["to_time"]

        time_diff += enddatetime - startdatetime

    current_frm_time_duration = get_current_permission_duration(from_date, to_date, from_time, to_time, False)
    added_time_diff = current_frm_time_duration + time_diff
    time_diff_in_min = int(str(time_diff).split(":")[0])*60 + int((str(time_diff)).split(":")[1])
    total_permission_duration = int(str(added_time_diff).split(":")[0])*60 + int((str(added_time_diff)).split(":")[1])
    get_allocated_permision_hours = frappe.get_single("Attendance Control Panel", "permission_durationin_hours")
    # permission_duration_allowed = frappe.get_single("control panel", "permission_hours")
    available_minutes = (get_allocated_permision_hours*60)-time_diff_in_min
    if total_permission_duration > get_allocated_permision_hours*60: #should get the value from control panel
            role_check = get_current_user_roles()
            if role_check == True:
                return {"Hr": True,"excess_minutes" : available_minutes}
            else:
                return {"Hr":False ,"excess_minutes" : available_minutes}


@frappe.whitelist()
def get_current_user_roles():
    role_list = ["HR Manager", "HR User"]
    # 
    user = frappe.get_doc("User", frappe.session.user)
    roles = [role.role for role in user.roles]
    for each_role in role_list:
        if each_role in roles:
            return True
    return False


@frappe.whitelist()
def get_current_permission_duration(from_date , to_date, from_time, to_time, convert = None):
    from_datetime = f"{from_date} {from_time}"
    from_datetime = datetime.strptime(from_datetime, "%Y-%m-%d %H:%M:%S")
    to_datetime = f"{to_date} {to_time}"
    to_datetime = datetime.strptime(to_datetime, "%Y-%m-%d %H:%M:%S")

    time_diff = to_datetime - from_datetime
    
    if time_diff >= timedelta(0) :

        if convert == None:
            total_permission_duration = int(str(time_diff).split(":")[0])*60 + int((str(time_diff)).split(":")[1])
            #this should also be changed to control panel minutes
            if total_permission_duration<0 or total_permission_duration>120 and get_current_user_roles() == False:
                return True
        elif convert == False:
            return time_diff
        elif convert == True:
            return total_permission_duration
        
    else:
        return True


@frappe.whitelist()
def get_available_permission():
    employee, employee_id = get_cur_user_id()
    if not employee == "Administrator":
        this_year = datetime.today().strftime("%Y")
        this_month = datetime.today().strftime("%m")
        this_day = date.today()
        last_day = last_day_of_month(date(int(this_year), int(this_month), 1))
        first_day = (date(int(this_year), int(this_month), 1))
        time_diff = timedelta()
        get_leave_allocation = frappe.get_all("Leave Allocation", filters = {
            "from_date" :["<=", datetime.now()],
            "to_date":[">=", datetime.now()],
            "employee" : employee_id[0],
            "leave_type": "Permission"
        })
        try :
            abc = get_leave_allocation[0]
            all_leave_application = frappe.get_all('Leave Application', filters={
                            'employee': employee_id[0],
                            'leave_type': "Permission",
                            'docstatus': 1, 
                            'from_date': ["between", [first_day,last_day]]
                        }, fields=['*'])
            for leave_application in all_leave_application:
                initial_startdate = datetime.combine(leave_application["from_date"], datetime.min.time())

                startdatetime = initial_startdate + leave_application["from_time"]

                initial_enddate = datetime.combine(leave_application["to_date"], datetime.min.time())

                enddatetime = initial_enddate + leave_application["to_time"]

                time_diff += enddatetime - startdatetime
            time_diff_in_min = int(str(time_diff).split(":")[0])*60 + int((str(time_diff)).split(":")[1])
            available_minutes = (2*60)-time_diff_in_min
            if available_minutes < 0:
                return 0

            return available_minutes
        except :
            return "NA"
    else:
        return "NA"


@frappe.whitelist()
def check_in_out(emp ,value, time):
    date_format = "%Y-%m-%d %H:%M:%S"
    time = datetime.strptime(time, date_format)
    check_in_doc = frappe.new_doc("Employee Checkin")
    check_in_doc.time = datetime.now()
    check_in_doc.employee = emp
    check_in_doc.log_type = value
    check_in_doc.time = time
    print(type(datetime.now()), type(time))
    check_in_doc.save()
    frappe.db.commit()
    return True



@frappe.whitelist()
def get_employee_id():
    user_id = frappe.session.user
    try:
        emp_id = frappe.get_all("Employee",{"user_id" : user_id},["name"])
        return {
            "value":True,
            "employee_id":emp_id[0]
        }
    except:
        return None



@frappe.whitelist()
def max_monthly_leave(leave_type):
    attendance_doc = frappe.get_single("Attendance Control Panel")
    print(attendance_doc.casual_leave_per_month)
    if leave_type == "Casual Leave":
        return int(attendance_doc.casual_leave_per_month)
    elif leave_type == "Sick Leave":
        return int(attendance_doc.sick_leave_leave_per_month)
    
    
@frappe.whitelist()
def monthly_available_leave(leave_type, cur_user):
    if not cur_user == "Administrator":
    
        leave_allocated_per_user = 0
        leave_applied = 0
        this_month = datetime.today().strftime("%m")
        this_year = datetime.today().strftime("%Y")
        
        user_id = get_cur_user_id()
        employee_id = user_id[1]
        attendance_control_panel = frappe.get_single("Attendance Control Panel")
        
        if leave_type == "Casual Leave":
            control_panel_leave = attendance_control_panel.casual_leave_per_month
        elif leave_type == "Sick Leave":
            control_panel_leave = attendance_control_panel.sick_leave_per_month
        
        last_day = last_day_of_month(date(int(this_year), int(12), 1))
        first_day = (date(int(this_year), int(1), 1))
        
        leave_allocated =  frappe.get_all("Leave Allocation", {
                "from_date" :["<=", datetime.now()],
                "to_date":[">=", datetime.now()],
                "employee" : employee_id[0],
                "leave_type": leave_type
            },["*"])
        
        all_leave_application = frappe.get_all('Leave Application', filters={
                    'employee': employee_id[0],
                    'leave_type': leave_type,
                    'docstatus': 1, 
                    'from_date': ["between", [first_day,last_day]]
                }, fields=['*'])
        if leave_allocated:
            for leave in leave_allocated:
                leave_allocated_per_user +=int(leave.new_leaves_allocated)
                

            for leave in all_leave_application:
                leave_applied += leave.total_leave_days
                
            leave_from_month = leave_allocated[0].from_date.strftime("%m")
            available_leave = ((((int(this_month)-int(leave_from_month))+1)*(int(control_panel_leave))) - int(leave_applied))
            return available_leave
        else:
            return "NA"
    else:
        return "NA"


@frappe.whitelist()
def monthly_available_casual_leave():
    leave_type = "Casual Leave"
    cur_user = frappe.session.user
    return (monthly_available_leave(leave_type, cur_user))

@frappe.whitelist()
def monthly_available_sick_leave():
    leave_type = "Sick Leave"
    cur_user = frappe.session.user
    return (monthly_available_leave(leave_type, cur_user))




@frappe.whitelist()
def checkin_out():
    employee , employee_id = get_cur_user_id()
    if employee_id != "Administrator":
        if employee_id != None:
            check_in_out_status = frappe.get_all("Employee Checkin", {"employee":employee_id[0]},["*"], order_by = "time desc")
            
            if check_in_out_status:
                last_status = check_in_out_status[0].log_type
            else:
                last_status = "OUT"
                
            if last_status == "IN":
                new_status = "OUT"
            else:
                new_status = "IN"
                
            check_in_out_doc = frappe.new_doc("Employee Checkin")
            check_in_out_doc.employee = employee_id[0]
            check_in_out_doc.log_type = new_status
            check_in_out_doc.time = datetime.now()
            check_in_out_doc.save()
            return new_status
        else:
            frappe.throw("Employee Id not Created")
            
            
            
@frappe.whitelist()            
def current_status():
    employee , employee_id = get_cur_user_id()
    if employee_id != "Administrator":
        if employee_id != None:
            check_in_out_status = frappe.get_all("Employee Checkin", {"employee":employee_id[0]},["*"], order_by = "time desc")
            if check_in_out_status:
                last_status = check_in_out_status[0].log_type
            else:
                last_status = "OUT"
                
            return last_status
        
        
        

@frappe.whitelist()
def get_employee_birthdays():
    bday_this_month_list = []
    this_year = datetime.today().strftime("%Y")
    this_month = datetime.today().strftime("%m")
    first_day = date(int(this_year), int(this_month), 1)
    last_day = last_day_of_month(date(int(this_year), int(this_month), 1))
    emp_details =  frappe.db.get_list(
        'Employee',
        fields=['employee_name', 'date_of_birth'],
        filters={'status': 'Active'},
        order_by='date_of_birth ASC'
    )
    for emp in emp_details:
        print(emp.date_of_birth.strftime("%m"))
        if emp.date_of_birth.strftime("%m") == this_month:
            bday_this_month_list.append(emp)
    if emp_details:
        return emp_details
    else:
        return None