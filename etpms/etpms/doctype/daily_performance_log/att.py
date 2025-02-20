import frappe
from datetime import timedelta

@frappe.whitelist()
def mark_attendance_for_payroll_period(payroll_period_name):
    """
    Marks attendance as "Present" and assigns 'Regular Day Shift' for all active employees
    for every day within the payroll period.

    Args:
        payroll_period_name (str): The name of the Payroll Period document.
                                   The document must have `start_date` and `end_date` fields.
    """
    try:
        # Fetch Payroll Period document
        payroll_period = frappe.get_doc("Payroll Period", payroll_period_name)

        # Get start and end dates
        start_date = frappe.utils.getdate(payroll_period.start_date)
        end_date = frappe.utils.getdate(payroll_period.end_date)

        # Fetch all active employees
        employees = frappe.get_all("Employee", filters={"status": "Active"}, fields=["name", "employee_name"])
        records_created = 0
        current_date = start_date

        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            for emp in employees:
                # Check if an Attendance record already exists for this employee on this date
                if not frappe.db.exists("Attendance", {"employee": emp.name, "attendance_date": date_str}):
                    att = frappe.new_doc("Attendance")
                    att.employee = emp.name
                    att.employee_name = emp.employee_name
                    att.attendance_date = date_str
                    att.status = "Present"
                    # Assign the shift value
                    att.shift = "Regular Day Shift"
                    att.insert(ignore_permissions=True)
                    records_created += 1
            current_date += timedelta(days=1)
        
        frappe.db.commit()
        return f"Attendance marked for {records_created} records in Payroll Period {payroll_period_name}"
    
    except Exception as e:
        frappe.log_error(f"Error marking attendance: {str(e)}", "Attendance Marking Error")
        frappe.throw(f"Failed to mark attendance: {str(e)}")
