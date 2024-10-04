# Copyright (c) 2024, droidal and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import getdate, today



def execute(filters=None):
	columns = get_columns()
	data = []

	year = int(getdate(today()).year)
	month = int(getdate(today()).month)

	start_date = f"{year}-{month:02d}-01"
	end_date = f"{year}-{month:02d}-{get_last_day_of_month(year, month)}"

	user_employee = frappe.get_value("Employee", {"user_id": frappe.session.user}, ["name", "employee_name"])
	if user_employee:
		user_employee = [user_employee]
		# Get attendance records for the month
		for emp in user_employee:

			attendance_records = frappe.get_all("Attendance", filters={
				"employee": emp[0],
				"attendance_date": ["between", [start_date, end_date]]
			}, fields=["attendance_date", "status"])

			# Count attendance statuses
			present_count = sum(1 for record in attendance_records if record["status"] == "Present")
			absent_count = sum(1 for record in attendance_records if record["status"] == "Absent")
			leave_count = sum(1 for record in attendance_records if record["status"] == "On Leave")
			
			data.append({
				"employee_name": emp[1],
				"present": int(present_count),
				"absent": int(absent_count),
				"leave":int(leave_count)
			})

		return columns, data

def get_columns():
	return [
		{"label": "Employee Name", "fieldname": "employee_name", "fieldtype": "Data", "width": 200},
		{"label": "Present", "fieldname": "present", "fieldtype": "Int", "width": 100},
		{"label": "Absent", "fieldname": "absent", "fieldtype": "Int", "width": 100},
		{"label": "On Leave", "fieldname": "on_leave", "fieldtype": "Int", "width": 100}
	]

def get_last_day_of_month(year, month):
	next_month = month % 12 + 1
	if next_month == 1:
		year += 1
	return (getdate(f"{year}-{next_month}-01") - getdate(f"{year}-{month:02d}-01")).days
