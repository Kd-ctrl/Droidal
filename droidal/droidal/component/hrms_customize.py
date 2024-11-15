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
    new_joinees_list = frappe.get_all("Employee", {},["employee_name", "date_of_joining"])
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
    first_in_record = None
    diff_time = None
    date = datetime.today().date()
    tomorrow = datetime.today().date()+timedelta(days=1)
    employee , employee_id = get_cur_user_id()
    if employee != "Administrator" and employee_id:
        employee_doc = frappe.get_all("Employee",{"name" : employee_id[0]},["*"])[0]
        employee_shift = employee_doc.default_shift
        if employee_shift:
            shift_doc = frappe.get_all("Shift Type",{"name":employee_shift},["*"])[0]
            if shift_doc.begin_check_in_before_shift_start_time:
                start_time_begin = shift_doc.begin_check_in_before_shift_start_time
            else:
                start_time_begin = 0
            if shift_doc.check_out_after_shift_end_time:
                end_time_begin = shift_doc.check_out_after_shift_end_time
            else:
                end_time_begin = 0
            start_time = shift_doc.start_time
            end_time = shift_doc.end_time
            if end_time> start_time:
                str_start_date_time = f"{date} {start_time}"
                str_end_date_time = f"{date} {end_time}"
            else:
                str_start_date_time = f"{date} {start_time}"
                str_end_date_time = f"{tomorrow} {end_time}"
                
            start_date_time = convert_str_to_datetime(str_start_date_time)
            end_date_time = convert_str_to_datetime(str_end_date_time)
            new_start_time = start_date_time - timedelta(minutes = start_time_begin)
            new_end_time = end_date_time + timedelta(minutes= end_time_begin)
            get_employee_check_in = frappe.get_all("Employee Checkin", {"time":["between",[new_start_time,new_end_time]],"employee" : employee_id[0]},["*"], order_by = "name asc")
            if get_employee_check_in:
                last_check_in = get_employee_check_in[-1]
                last_log_type = last_check_in.log_type
                for employee_check_in in get_employee_check_in:
                    if first_in_record == None:
                        if employee_check_in.log_type == "IN":
                            first_in_record = employee_check_in.name
                            in_time = employee_check_in.time
                    elif first_in_record != None:
                        if employee_check_in.log_type == "OUT":
                            out_time = employee_check_in.time
                            if diff_time != None:
                                diff_time += out_time - in_time
                            else:
                                diff_time = out_time - in_time
                        elif employee_check_in.log_type == "IN":
                            in_time = employee_check_in.time  
                            
                if diff_time == None:
                    overall_time = (datetime.today() - in_time)
                elif last_log_type == "IN":
                    overall_time = diff_time + (datetime.today() - in_time)
                else:
                    overall_time = diff_time
                
                split_time = str(overall_time).split(":")
                hrs = split_time[0]
                min = split_time[1]
                sec = split_time[2].split(".")[0]
                return (f"{hrs}:{min}:{sec}",last_log_type, new_start_time, new_end_time, employee_id[0])
            else:
                return "NA"        
        else:
            return "NA"
    else:
        return "NA"    
            
            
            
            
def convert_str_to_datetime(str):
    new_datetime = datetime.strptime(str, "%Y-%m-%d %H:%M:%S")
    return new_datetime


@frappe.whitelist()
def check_current_log_type(start_time, end_time, emp_id):
    get_employee_check_in = frappe.get_all("Employee Checkin", {"time":["between",[start_time,end_time]],"employee" : emp_id},["*"], order_by = "name asc")
    if get_employee_check_in:
        last_check_in = get_employee_check_in[-1]
        last_log_type = last_check_in.log_type
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