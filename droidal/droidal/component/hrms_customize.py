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
                # print(allocations)
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
    # print(type(datetime.now()), type(time))
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
    # print(attendance_doc.casual_leave_per_month)
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
            
            available_leave = leave_allocated_per_user - leave_applied    
            # leave_from_month = leave_allocated[0].from_date.strftime("%m")
            # available_leave = ((((int(this_month)-int(leave_from_month))+1)*(int(control_panel_leave))) - int(leave_applied))
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
    this_day = datetime.today().strftime("%d")
    this_year = datetime.today().strftime("%Y")
    this_month = datetime.today().strftime("%m")
    if int(this_month) == 12:
        next_month= 1
    else:
        next_month = int(this_month)+1
    today = datetime.today()
    # last_date = last_day_of_month(date(int(this_year), int(this_month), 1)).strftime("%d")
    # last_day = today + timedelta(days=int(last_date))
    first_day = date(int(this_year), int(this_month), 1)
    last_day = last_day_of_month(date(int(this_year), int(this_month), 1))
    emp_details =  frappe.get_all(
        'Employee',
        fields=['employee_name', 'date_of_birth'],
        filters={'status': 'Active',
                #  "date_of_birth":["between",[first_day,last_day]]
                 },
        order_by='date_of_birth ASC'
    )
    date_list = []
    for emp in emp_details:
        # print(emp.date_of_birth.strftime("%m"))
        if emp.date_of_birth.strftime("%m") == this_month and int(emp.date_of_birth.strftime("%d")) >= int(this_day)or emp.date_of_birth.strftime("%m") == str(next_month):
            date_list.append(emp.date_of_birth)
            bday_this_month_list.append(emp)
    # print(date_list)
    sorted_dates = sorted(date_list, key=lambda date: date.month)
    # print(sorted_dates)
    bday_month_list = []
    for each_day in sorted_dates:
        for each_bday in bday_this_month_list:
            if each_day == each_bday.date_of_birth:
                bday_this_month_list.remove(each_bday)
                bday_month_list.append(each_bday)
     
    month_day = []           
    for every_birthday in bday_month_list:
        months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        every_birthday.date_of_birth = f"{months[int(every_birthday.date_of_birth.month)-1]} {every_birthday.date_of_birth.day}"
        month_day.append(every_birthday.date_of_birth)
    
    sorted_dates = sorted(month_day, key=lambda date: datetime.strptime(date, "%B %d"))
    
    finished_bday_list = []
    for each_day in sorted_dates:
        for each_bday in bday_month_list:
            if each_day == each_bday.date_of_birth:
                bday_month_list.remove(each_bday)
                finished_bday_list.append(each_bday)
        
    if finished_bday_list:
        return finished_bday_list
    else:
        return None
    
    
    
@frappe.whitelist()
def get_new_joinees():
    this_month_joinees = []
    this_year = datetime.today().strftime("%Y")
    this_month = datetime.today().strftime("%m")
    last_day = datetime.today()
    first_day = last_day - timedelta(days=30)
    
    # last_date = last_day_of_month(date(int(this_year), int(this_month), 1))
    # first_day = date(int(this_year), int(this_month), 1)
    new_joinees_list = frappe.get_all("Employee", {"date_of_joining":["between",[first_day,last_day]]},["employee_name"],order_by = "date_of_joining desc")
    for emp in new_joinees_list:
        this_month_joinees.append(emp.employee_name)
    return this_month_joinees


@frappe.whitelist()
def get_anniversary():
    anniversary_list = []
    this_year = datetime.today().strftime("%Y")
    this_month = datetime.today().strftime("%m")
    this_day = datetime.today().strftime("%d")
    today = datetime.today()
    last_date = last_day_of_month(date(int(this_year), int(this_month), 1)).strftime("%d")
    last_day = today + timedelta(days=int(last_date))
    if int(this_month) == 12:
        next_month= 1
    else:
        next_month = int(this_month)+1

    # first_day = date(int(this_year), int(this_month), 1)
   
    
    # "date_of_joining":["between",[first_day,last_day]]
    new_joinees_list = frappe.get_all("Employee", {'status': 'Active'},["employee_name", "date_of_joining"])
    for emp in new_joinees_list:
        if emp.date_of_joining.strftime("%m") == this_month and emp.date_of_joining.strftime("%Y") != this_year and int(emp.date_of_joining.strftime("%d")) >= int(this_day) or emp.date_of_joining.strftime("%m") == str(next_month) :
                anniversary_list.append(emp)
    return anniversary_list


@frappe.whitelist()
def get_upcoming_leaves():
    employee , employee_id = get_cur_user_id()
    if employee != "Administrator" and employee_id:
        employee_doc = frappe.get_doc("Employee",employee_id)
        user_holiday_list = employee_doc.holiday_list
        if user_holiday_list:
            holiday_list = frappe.get_all("Holiday",{"weekly_off":False, "parent":user_holiday_list},["description","holiday_date"],order_by= "holiday_date asc")
            return holiday_list
        
        
        
@frappe.whitelist()
def current_work_timings():
    from datetime import datetime
    employee, employee_id = get_cur_user_id()
    if employee != "Administrator" and employee_id:
        checkins = frappe.get_all(
            "Employee Checkin",
            {"employee": employee_id[0]},
            ["*"],
            order_by="time desc"
        )
        for record in checkins:  # Find the latest "IN"
            if record.log_type == "IN":
                last_in_time = record.time
                # Optionally, check if it is after an "OUT" (for robust logic)
                elapsed = datetime.now() - last_in_time
                hrs, rem = divmod(elapsed.total_seconds(), 3600)
                mins, secs = divmod(rem, 60)
                return f"{int(hrs)}:{int(mins)}:{int(secs)}", "IN", employee_id[0]
            
            elif record.log_type == "OUT":
                return "0:0:0", "OUT", employee_id[0]
        return "NA"
    else:
        return "NA"

            
            
            
            
def convert_str_to_datetime(str):
    new_datetime = datetime.strptime(str, "%Y-%m-%d %H:%M:%S")
    return new_datetime


@frappe.whitelist()
def check_current_log_type(emp_id):
    get_employee_check_in = frappe.get_all("Employee Checkin", {"employee" : emp_id},["*"], order_by = "name asc")
    if get_employee_check_in:
        last_check_in = get_employee_check_in[-1]
        last_log_type = last_check_in.log_type

        if last_check_in.log_type == "IN":
        #     last_in_time = last_check_in.time
        #     # Optionally, check if it is after an "OUT" (for robust logic)
        #     elapsed = datetime.now() - last_in_time
        #     hrs, rem = divmod(elapsed.total_seconds(), 3600)

        #     if int(hrs)>7:
        #         check_out_doc = frappe.get_doc({
        #                 "doctype": "Employee Checkin",
        #                 "employee": emp_id,
        #                 "time": datetime.now(),           
        #                 "log_type": "OUT",        
        #             })
        #         check_out_doc.insert()
        #         frappe.db.commit()
            return last_log_type
    else:
        return "NA"
    
    
    

@frappe.whitelist()
def get_active_employees():
    employee_list =[]
    active_employees = []
    # Fetch active employees (you can modify the filter as needed)
    employees = frappe.get_all("Employee",{"status":"Active"},["name","employee_name"])
    
    for employee in employees:
        check_in_out_status = frappe.get_all("Employee Checkin", {"employee":employee["name"]},["log_type"], order_by = "time desc")
        if check_in_out_status and check_in_out_status[0].log_type == "IN":
            active_employees.append([employee["employee_name"],check_in_out_status[0].log_type])
    for employee in employees:
        check_in_out_status = frappe.get_all("Employee Checkin", {"employee":employee["name"]},["log_type"], order_by = "time desc")
        if check_in_out_status and check_in_out_status[0].log_type == "OUT":
            active_employees.append([employee["employee_name"],check_in_out_status[0].log_type])
    for employee in employees:
        if employee["employee_name"] not in [item for sublist in active_employees for item in sublist]:
            active_employees.append([employee["employee_name"],"OUT"])
    return active_employees


@frappe.whitelist()
def get_employees_with_stars():
    this_year = datetime.today().strftime("%Y")
    this_month = datetime.today().strftime("%m")
    this_day = date.today()
    last_day = last_day_of_month(date(int(this_year), int(this_month), 1))
    first_day = (date(int(this_year), int(this_month), 1))
    emp_all = frappe.get_all('Task',{},["*"])
    emp_with_star = frappe.get_all(
        'Task',
        fields=['name', 'custom_assign_to','custom_rating','custom_employee_name'],
        filters={"completed_on":["Between",[first_day,last_day]]},
        order_by='custom_rating desc'
    )
    get_emp_list = frappe.get_all("Employee",filters = {"status":"Active"},pluck = "name")
    emp_dict= {}
    for each_emp in get_emp_list:
        per_emp_star = 0
        for emp in emp_all:
            if each_emp == emp.custom_assign_to:
                if emp.custom_rating:
                    per_emp_star += emp.custom_rating
        emp_dict[emp.custom_employee_name] = per_emp_star * 5
        
    sorted_employees = sorted(
        [{"employee": emp, "star_count": stars} for emp, stars in emp_dict.items() if stars > 0],
        key=lambda x: x["star_count"],
        reverse=True
    )
    return sorted_employees



@frappe.whitelist()
def get_rockstar():
    this_year = datetime.today().strftime("%Y")
    this_month = datetime.today().strftime("%m")
    this_day = date.today()
    last_day = last_day_of_month(date(int(this_year), int(this_month), 1))
    first_day = (date(int(this_year), int(this_month), 1))
    emp = frappe.get_all("Employee Of the Month",filters={"posting_date":["Between",[first_day,last_day]]},fields =["*"])
    return emp



# @frappe.whitelist()
# def logout_employee():
#     employee_list= frappe.get_all("Employee",{"status":"active"},["name"])
#     for employee in employee_list:
#         get_employee_check_in = frappe.get_all("Employee Checkin", {"employee" : employee.name},["*"], order_by = "name asc")
#         if get_employee_check_in:
#             last_check_in = get_employee_check_in[-1]
#             last_log_type = last_check_in.log_type

#             if last_check_in.log_type == "IN":
#                 last_in_time = last_check_in.time
#                 # Optionally, check if it is after an "OUT" (for robust logic)
#                 elapsed = datetime.now() - last_in_time
#                 hrs, rem = divmod(elapsed.total_seconds(), 3600)

#                 if int(hrs)>7:
#                     check_out_doc = frappe.get_doc({
#                             "doctype": "Employee Checkin",
#                             "employee": employee.name,
#                             "time": datetime.now(),           
#                             "log_type": "OUT",        
#                         })
#                     check_out_doc.insert()
#                     frappe.db.commit()
#                 return last_log_type
#         else:
#             return "NA"

import frappe
from datetime import datetime, timedelta, date
from frappe.utils import getdate, date_diff, today
import calendar

def last_day_of_month(any_day):
    next_month = any_day.replace(day=28) + timedelta(days=4)
    return next_month - timedelta(days=next_month.day)

@frappe.whitelist()
def get_available_leaves():
    employee, employee_id = get_cur_user_id()
    if employee != "Administrator" and employee_id:
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
                    'to_date': [">", this_day]
                }, fields=['*'])
                
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
                    
                    available_leaves = int(total_allocated) - total_taken
                    total_leaves += available_leaves
        return total_leaves 
    else:
        return "NA"

def get_cur_user_id():
    employee = frappe.session.user
    if employee != "Administrator":
        employee_id = frappe.get_all("Employee", {"user_id": employee}, pluck="name")
        if employee_id:
            return employee, employee_id
    return employee, None

@frappe.whitelist()
def create_salary_slip_with_start_date_logic(employee_id, month_name, year=None):
    """
    Calculate payroll and create Salary Slip with start date logic
    Uses employee start date if it's after month start, otherwise uses month start
    """
    
    # If year not provided, use current year
    if not year:
        year = datetime.now().year
    
    # Convert month name to month number
    month_map = {
        'january': 1, 'february': 2, 'march': 3, 'april': 4,
        'may': 5, 'june': 6, 'july': 7, 'august': 8,
        'september': 9, 'october': 10, 'november': 11, 'december': 12
    }
    
    month_num = month_map.get(month_name.lower())
    if not month_num:
        frappe.throw(f"Invalid month name: {month_name}")
    
    # Get month start and end dates
    month_start_date = datetime(year, month_num, 1).date()
    last_day = calendar.monthrange(year, month_num)[1]
    month_end_date = datetime(year, month_num, last_day).date()
    
    # Get employee details
    employee = frappe.get_doc("Employee", employee_id)
    
    # Determine start date based on employee date_of_joining
    employee_start_date = employee.date_of_joining
    
    if employee_start_date and employee_start_date > month_start_date:
        start_date = employee_start_date
    else:
        start_date = month_start_date
    
    end_date = month_end_date
    
    # Convert to string format for processing
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    # Get salary components from employee doctype
    salary_components = frappe.get_all(
        "Salary Details",
        filters={"parent": employee_id},
        fields=["salary_component", "amount", "parentfield"]
    )
    
    salary_components_earnings = {}
    salary_components_deductions = {}
    
    for component in salary_components:
        if component.parentfield == "custom_earnings":
            salary_components_earnings[component.salary_component] = component.amount
        elif component.parentfield == "custom_deductions":
            salary_components_deductions[component.salary_component] = component.amount
    
    # Calculate total monthly salary
    total_earnings = sum(salary_components_earnings.values())
    total_deductions = sum(salary_components_deductions.values())
    total_monthly_salary = total_earnings - total_deductions
    
    # Convert dates to datetime objects
    start_dt = datetime.strptime(start_date_str, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date_str, '%Y-%m-%d')
    total_days_in_period = (end_dt - start_dt).days + 1
    
    # Get total days in the month for per-day calculation
    total_days_in_month = calendar.monthrange(year, month_num)[1]
    
    # Get attendance records for the period
    attendance_records = frappe.get_all(
        "Attendance",
        filters={
            "employee": employee_id,
            "attendance_date": ["between", [start_date_str, end_date_str]]
        },
        fields=["attendance_date", "status"]
    )
    
    # Count worked days (Present status)
    worked_days = len([record for record in attendance_records if record.status == "Present"])
    
    # Count weekends (Saturday and Sunday) in the period
    weekend_days = 0
    current_date = start_dt
    while current_date <= end_dt:
        if current_date.weekday() in [5, 6]:  # Saturday = 5, Sunday = 6
            weekend_days += 1
        current_date += timedelta(days=1)
    
    # Calculate payable days (worked days + weekends)
    payable_days = worked_days + weekend_days
    
    # Calculate per day salary based on monthly total
    per_day_salary = total_monthly_salary / total_days_in_month
    
    # Calculate component-wise breakdown for earnings
    calculated_earnings = {}
    for component, amount in salary_components_earnings.items():
        per_day_component = amount / total_days_in_month
        calculated_earnings[component] = per_day_component * payable_days
    
    # Calculate component-wise breakdown for deductions
    calculated_deductions = {}
    for component, amount in salary_components_deductions.items():
        per_day_component = amount / total_days_in_month
        calculated_deductions[component] = per_day_component * payable_days
    
    total_payable_earnings = sum(calculated_earnings.values())
    total_payable_deductions = sum(calculated_deductions.values())
    total_payable_salary = total_payable_earnings - total_payable_deductions
    
    # Create Salary Slip document
    salary_slip = frappe.new_doc("Salary Slip")
    
    # Set basic fields
    salary_slip.employee = employee_id
    salary_slip.employee_name = employee.employee_name
    salary_slip.department = employee.department
    salary_slip.designation = employee.designation
    salary_slip.company = employee.company
    salary_slip.start_date = start_date_str
    salary_slip.end_date = end_date_str
    salary_slip.posting_date = frappe.utils.today()
    salary_slip.total_working_days = total_days_in_period
    salary_slip.payment_days = payable_days
    salary_slip.leave_without_pay = total_days_in_period - payable_days
    
    # Add earnings (salary components)
    for component_name, calculated_amount in calculated_earnings.items():
        if calculated_amount > 0:
            salary_slip.append("earnings", {
                "salary_component": component_name,
                "amount": calculated_amount
            })
    
    # Add deductions
    for component_name, calculated_amount in calculated_deductions.items():
        if calculated_amount > 0:
            salary_slip.append("deductions", {
                "salary_component": component_name,
                "amount": calculated_amount
            })
    
    # Set totals
    salary_slip.gross_pay = total_payable_earnings
    salary_slip.total_deduction = total_payable_deductions
    salary_slip.net_pay = total_payable_salary
    
    # Add custom fields for tracking (make sure these fields exist in Salary Slip)
    if hasattr(salary_slip, 'custom_worked_days'):
        salary_slip.custom_worked_days = worked_days
    if hasattr(salary_slip, 'custom_weekend_days'):
        salary_slip.custom_weekend_days = weekend_days
    if hasattr(salary_slip, 'custom_per_day_salary'):
        salary_slip.custom_per_day_salary = per_day_salary
    
    # Save and submit the salary slip
    salary_slip.insert()
    salary_slip.submit()
    
    return {
        'salary_slip_id': salary_slip.name,
        'employee_id': employee_id,
        'employee_name': employee.employee_name,
        'month': month_name.title(),
        'year': year,
        'employee_joining_date': str(employee_start_date) if employee_start_date else None,
        'month_start_date': str(month_start_date),
        'actual_start_date': start_date_str,
        'end_date': end_date_str,
        'total_days_in_period': total_days_in_period,
        'total_days_in_month': total_days_in_month,
        'worked_days': worked_days,
        'weekend_days': weekend_days,
        'payable_days': payable_days,
        'gross_pay': total_payable_earnings,
        'total_deductions': total_payable_deductions,
        'net_pay': total_payable_salary,
        'per_day_salary': per_day_salary,
        'earnings_components': calculated_earnings,
        'deduction_components': calculated_deductions,
        'message': f'Salary Slip {salary_slip.name} created successfully'
    }

# Rest of your functions remain the same...
