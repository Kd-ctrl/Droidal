# salary_calculations.py - Standalone functions for salary calculations

import frappe
from datetime import datetime
import math
import calendar




#need to add basic and pay month also , working_days , and present_days in employee_data
def initialize_sample_data(get_employee=None):
    """Initialize with sample data if not provided"""
    
    
    employee_data = {
        'employee_name': get_employee.get('employee_name', ""),
        'employee_id': get_employee.get('employee_id', ""),
        'designation': get_employee.get('designation', ""),
        'department': get_employee.get('department', ""),
        'pan_number': get_employee.get('pan_number', ""),
        'uan_number': get_employee.get('uan_number', ""),
        'bank_account': get_employee.get('bank_account', ""),
    }
    return employee_data





def get_year_month_date(month_name=None, year=None,get_employee=None):
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

    
    # Determine start date based on employee date_of_joining
    employee_start_date = get_employee.date_of_joining
    
    if employee_start_date and employee_start_date > month_start_date:
        start_date = employee_start_date
    else:
        start_date = month_start_date
    
    end_date = month_end_date
    
    # Convert to string format for processing
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    return start_date_str, end_date_str

    # Calculate working days and present days



def get_employee_working_days(get_employee, end_date, start_date):
    """Calculate working days and present days for the employee"""

    holiday = get_employee.get('holiday')
    if holiday:
        holidays = frappe.get_all("Holiday", filters={
            'holiday_date': ['between', [start_date, end_date]],
            'holiday_list': holiday
        }, fields=['holiday_date'])




    if not holiday:
        holidays = frappe.get_all("Holiday List", filters={
        'holiday_date': ['between', [start_date, end_date]]
        }, fields=['holiday_date'])

        

    # Assuming a standard month with 22 working days


    working_days = 22
    
    # Get employee's attendance data
    attendance = frappe.get_all("Attendance", filters={
        'employee': get_employee.name,
        'attendance_date': ['between', [get_employee.date_of_joining, datetime.now().date()]]
    }, fields=['attendance_date', 'status'])
    
    present_days = sum(1 for att in attendance if att.status == 'Present')
    
    return {
        'working_days': working_days,
        'present_days': present_days
    }

def calculate_earnings(basic_salary, is_metro_city=1):
    """Calculate all earnings components"""
    
    basic = basic_salary
    
    earnings = {
        'basic_salary': basic,
        'dearness_allowance': basic * 0.12,  # 12% of basic
        'house_rent_allowance': basic * (0.50 if is_metro_city else 0.40),
        'conveyance_allowance': 2400,  # Standard amount
        'leave_travel_allowance': basic * 0.10,
        'medical_allowance': 15000,  # Annual limit
        'special_allowance': basic * 0.20,
        'meal_coupons': 2200,  # Monthly limit ₹26,400 annually
        'phone_allowance': 2000,  # Tax-exempt for official use
        'uniform_allowance': 1500,  # Fully tax-exempt
        'children_education_allowance': 200,  # ₹100 per child, max 2 children
        'children_hostel_allowance': 600,  # ₹300 per child, max 2 children
        'car_maintenance_allowance': 2700,  # For cars up to 1600cc
        'performance_bonus': basic * 0.08,
        'overtime_amount': 3000
    }
    
    # Calculate gross salary
    earnings['gross_salary'] = sum(earnings.values()) - earnings['basic_salary'] + basic
    
    return earnings

def calculate_tax_exemptions(earnings, basic_salary, is_metro_city=1):
    """Calculate tax-exempt portions of allowances"""
    
    basic = basic_salary
    
    # HRA Exemption Calculation
    actual_hra = earnings['house_rent_allowance']
    rent_paid = basic * 0.60  # Assuming rent is 60% of basic
    excess_rent = max(0, rent_paid - (basic * 0.10))
    hra_limit = basic * (0.50 if is_metro_city else 0.40)
    hra_exemption = min(actual_hra, excess_rent, hra_limit)
    
    # LTA Exemption (assuming travel bills available)
    lta_exemption = min(earnings['leave_travel_allowance'], basic * 0.10)
    
    # Medical Allowance Exemption (with bills)
    medical_exemption = min(earnings['medical_allowance'], 15000)
    
    # Fully exempt allowances
    meal_coupons_exemption = min(earnings['meal_coupons'], 2200)
    phone_allowance_exemption = earnings['phone_allowance']  # Fully exempt for official use
    uniform_allowance_exemption = earnings['uniform_allowance']  # Fully exempt
    children_education_exemption = earnings['children_education_allowance']  # Fully exempt
    children_hostel_exemption = earnings['children_hostel_allowance']  # Fully exempt
    car_maintenance_exemption = earnings['car_maintenance_allowance']  # Within limits
    
    exemptions = {
        'hra_exemption': hra_exemption,
        'lta_exemption': lta_exemption,
        'medical_exemption': medical_exemption,
        'meal_coupons_exemption': meal_coupons_exemption,
        'phone_allowance_exemption': phone_allowance_exemption,
        'uniform_allowance_exemption': uniform_allowance_exemption,
        'children_education_exemption': children_education_exemption,
        'children_hostel_exemption': children_hostel_exemption,
        'car_maintenance_exemption': car_maintenance_exemption
    }
    
    # Total exemptions
    total_exemptions = sum(exemptions.values())
    
    # Taxable income after exemptions
    taxable_income = earnings['gross_salary'] - total_exemptions
    
    exemptions['total_exemptions'] = total_exemptions
    exemptions['taxable_income'] = taxable_income
    
    return exemptions

def calculate_income_tax(annual_income):
    """Calculate income tax based on new tax regime 2024-25"""
    
    tax = 0
    
    # New Tax Regime Slabs (2024-25)
    if annual_income > 300000:
        # 5% on income from ₹3,00,001 to ₹7,00,000
        tax += min(annual_income - 300000, 400000) * 0.05
    
    if annual_income > 700000:
        # 10% on income from ₹7,00,001 to ₹10,00,000
        tax += min(annual_income - 700000, 300000) * 0.10
    
    if annual_income > 1000000:
        # 15% on income from ₹10,00,001 to ₹12,00,000
        tax += min(annual_income - 1000000, 200000) * 0.15
    
    if annual_income > 1200000:
        # 20% on income from ₹12,00,001 to ₹15,00,000
        tax += min(annual_income - 1200000, 300000) * 0.20
    
    if annual_income > 1500000:
        # 30% on income above ₹15,00,000
        tax += (annual_income - 1500000) * 0.30
    
    # Add 4% Health and Education Cess
    tax_with_cess = tax * 1.04
    
    return tax_with_cess

def calculate_deductions(earnings, exemptions, basic_salary):
    """Calculate all deductions"""
    
    basic = basic_salary
    gross = earnings['gross_salary']
    taxable_income = exemptions['taxable_income']
    
    # Employee Provident Fund (EPF) - 12% of basic
    epf_employee = basic * 0.12
    
    # Employees' State Insurance (ESI) - 0.75% of gross (if applicable)
    # ESI applicable if gross salary <= ₹25,000
    if gross <= 25000:
        esi_employee = gross * 0.0075
    else:
        esi_employee = 0
    
    # Professional Tax (PT) - varies by state, sample for Maharashtra
    if gross <= 10000:
        professional_tax = 175
    elif gross <= 25000:
        professional_tax = 300
    else:
        professional_tax = 300
    
    # Standard Deduction (New Tax Regime)
    annual_standard_deduction = 75000
    monthly_standard_deduction = annual_standard_deduction / 12
    
    # Calculate annual taxable income for TDS
    annual_taxable = (taxable_income - monthly_standard_deduction) * 12
    
    # Income Tax Calculation
    annual_tax = calculate_income_tax(annual_taxable)
    tds = annual_tax / 12
    
    # Other deductions
    group_insurance = 500
    loan_emi = 5000
    canteen_charges = 800
    
    deductions = {
        'epf_employee': epf_employee,
        'esi_employee': esi_employee,
        'professional_tax': professional_tax,
        'tds': tds,
        'group_insurance': group_insurance,
        'loan_emi': loan_emi,
        'canteen_charges': canteen_charges
    }
    
    # Total deductions
    deductions['total_deductions'] = sum(deductions.values())
    
    return deductions

def calculate_net_salary(earnings, deductions):
    """Calculate final net salary and YTD figures"""
    
    net_salary = earnings['gross_salary'] - deductions['total_deductions']
    
    # Year-to-date calculations (assuming this is calculated monthly)
    month_number = datetime.now().month
    
    summary = {
        'net_salary': net_salary,
        'ytd_gross': earnings['gross_salary'] * month_number,
        'ytd_deductions': deductions['total_deductions'] * month_number,
        'ytd_net': net_salary * month_number
    }
    
    return summary

def generate_complete_salary_slip(emp_id=None, month_name=None, year=None):
    """Generate complete salary slip with all calculations"""
    get_employee = frappe.get_doc("Employee", emp_id)
    
    # Initialize data
    data = initialize_sample_data(get_employee)

    start_date, end_date = get_year_month_date(month_name, year,get_employee)

    no_of_working_days = get_employee_working_days( get_employee, end_date, start_date)
    
    # Calculate earnings
    earnings = calculate_earnings(data['basic_salary'], data['is_metro_city'])
    
    # Calculate tax exemptions
    exemptions = calculate_tax_exemptions(earnings, data['basic_salary'], data['is_metro_city'])
    
    # Calculate deductions
    deductions = calculate_deductions(earnings, exemptions, data['basic_salary'])
    
    # Calculate net salary
    summary = calculate_net_salary(earnings, deductions)
    
    # Combine all data
    complete_slip = {
        'employee_details': {
            'company_name': 'ABC Technologies Pvt Ltd',
            'company_address': '123 Tech Park, Bangalore - 560001',
            'company_tan': 'BLRA12345B',
            'employee_name': data['employee_name'],
            'employee_id': data['employee_id'],
            'designation': data['designation'],
            'department': data['department'],
            'pan_number': data['pan_number'],
            'uan_number': data['uan_number'],
            'bank_account': data['bank_account'],
            'pay_month': data['pay_month'],
            'working_days': data['working_days'],
            'present_days': data['present_days']
        },
        'earnings': earnings,
        'exemptions': exemptions,
        'deductions': deductions,
        'summary': summary
    }
    
    return complete_slip

def print_salary_slip(salary_data):
    """Format and print salary slip"""
    
    print("=" * 60)
    print(f"SALARY SLIP - {salary_data['employee_details']['pay_month']}")
    print("=" * 60)
    
    # Company Details
    print(f"Company: {salary_data['employee_details']['company_name']}")
    print(f"Address: {salary_data['employee_details']['company_address']}")
    print(f"TAN: {salary_data['employee_details']['company_tan']}")
    print()
    
    # Employee Details
    emp = salary_data['employee_details']
    print("EMPLOYEE DETAILS:")
    print(f"Name: {emp['employee_name']} | ID: {emp['employee_id']}")
    print(f"Designation: {emp['designation']} | Department: {emp['department']}")
    print(f"PAN: {emp['pan_number']} | UAN: {emp['uan_number']}")
    print(f"Working Days: {emp['working_days']} | Present Days: {emp['present_days']}")
    print()
    
    # Earnings
    print("EARNINGS:")
    print("-" * 40)
    for key, value in salary_data['earnings'].items():
        if key != 'gross_salary':
            print(f"{key.replace('_', ' ').title():30s} : ₹{value:,.2f}")
    print("-" * 40)
    print(f"{'GROSS SALARY':30s} : ₹{salary_data['earnings']['gross_salary']:,.2f}")
    print()
    
    # Tax Exemptions
    print("TAX EXEMPTIONS:")
    print("-" * 40)
    for key, value in salary_data['exemptions'].items():
        if key not in ['total_exemptions', 'taxable_income']:
            print(f"{key.replace('_', ' ').title():30s} : ₹{value:,.2f}")
    print("-" * 40)
    print(f"{'TOTAL EXEMPTIONS':30s} : ₹{salary_data['exemptions']['total_exemptions']:,.2f}")
    print(f"{'TAXABLE INCOME':30s} : ₹{salary_data['exemptions']['taxable_income']:,.2f}")
    print()
    
    # Deductions
    print("DEDUCTIONS:")
    print("-" * 40)
    for key, value in salary_data['deductions'].items():
        if key != 'total_deductions':
            print(f"{key.replace('_', ' ').title():30s} : ₹{value:,.2f}")
    print("-" * 40)
    print(f"{'TOTAL DEDUCTIONS':30s} : ₹{salary_data['deductions']['total_deductions']:,.2f}")
    print()
    
    # Summary
    print("SUMMARY:")
    print("-" * 40)
    print(f"{'Gross Salary':30s} : ₹{salary_data['earnings']['gross_salary']:,.2f}")
    print(f"{'Total Deductions':30s} : ₹{salary_data['deductions']['total_deductions']:,.2f}")
    print(f"{'NET SALARY':30s} : ₹{salary_data['summary']['net_salary']:,.2f}")
    print()
    
    # YTD Summary
    print("YEAR TO DATE:")
    print("-" * 40)
    print(f"{'YTD Gross':30s} : ₹{salary_data['summary']['ytd_gross']:,.2f}")
    print(f"{'YTD Deductions':30s} : ₹{salary_data['summary']['ytd_deductions']:,.2f}")
    print(f"{'YTD Net':30s} : ₹{salary_data['summary']['ytd_net']:,.2f}")
    print("=" * 60)

@frappe.whitelist()
def create_salary_slip_api(employee_data=None):
    """API method to create salary slip"""
    
    if isinstance(employee_data, str):
        import json
        employee_data = json.loads(employee_data)
    
    salary_slip = generate_complete_salary_slip(employee_data)
    
    return salary_slip

@frappe.whitelist()
def get_salary_breakdown_api(basic_salary, is_metro_city=1):
    """API method to get detailed salary breakdown"""
    
    basic_salary = float(basic_salary)
    is_metro_city = int(is_metro_city)
    
    earnings = calculate_earnings(basic_salary, is_metro_city)
    exemptions = calculate_tax_exemptions(earnings, basic_salary, is_metro_city)
    deductions = calculate_deductions(earnings, exemptions, basic_salary)
    summary = calculate_net_salary(earnings, deductions)
    
    return {
        'basic_calculations': {
            'basic_salary': basic_salary,
            'gross_salary': earnings['gross_salary'],
            'taxable_income': exemptions['taxable_income'],
            'total_exemptions': exemptions['total_exemptions'],
            'net_salary': summary['net_salary']
        },
        'detailed_breakdown': {
            'earnings': earnings,
            'exemptions': exemptions,
            'deductions': deductions,
            'summary': summary
        }
    }

# Usage Examples
if __name__ == "__main__":
    
    # Example 1: Generate salary slip with default data
    print("Example 1: Default Salary Slip")
    salary_slip_1 = generate_complete_salary_slip()
    print_salary_slip(salary_slip_1)
    
    print("\n" + "="*80 + "\n")
    
    # Example 2: Generate salary slip with custom data
    print("Example 2: Custom Salary Slip")
    custom_data = {
        'employee_name': 'Priya Sharma',
        'employee_id': 'EMP002',
        'basic_salary': 75000,
        'designation': 'Senior Developer',
        'department': 'Technology',
        'is_metro_city': 0  # Non-metro city
    }
    
    salary_slip_2 = generate_complete_salary_slip(custom_data)
    print_salary_slip(salary_slip_2)

# Test individual functions
def test_calculations():
    """Test individual calculation functions"""
    
    basic = 60000
    is_metro = 1
    
    print("Testing Individual Functions:")
    print("-" * 40)
    
    # Test earnings
    earnings = calculate_earnings(basic, is_metro)
    print(f"Gross Salary: ₹{earnings['gross_salary']:,.2f}")
    
    # Test exemptions
    exemptions = calculate_tax_exemptions(earnings, basic, is_metro)
    print(f"Total Exemptions: ₹{exemptions['total_exemptions']:,.2f}")
    print(f"Taxable Income: ₹{exemptions['taxable_income']:,.2f}")
    
    # Test deductions
    deductions = calculate_deductions(earnings, exemptions, basic)
    print(f"Total Deductions: ₹{deductions['total_deductions']:,.2f}")
    
    # Test net salary
    summary = calculate_net_salary(earnings, deductions)
    print(f"Net Salary: ₹{summary['net_salary']:,.2f}")
