# Copyright (c) 2025, Elif Technologies PLC and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class DailyPerformanceLog(Document):
    def on_submit(self):
        self.update_project_activity()
        self.update_activity_performance_to_date()

    def on_cancel(self):
        self.cancel_update_project_activity()
        self.update_activity_performance_to_date()

    def update_project_activity(self):
        # Ensure a Project Activity is linked
        if not self.project_activity:
            frappe.throw("Project Activity is not linked")

        # --- 1. Update the linked Project Activity ---
        project_activity = frappe.get_doc("Project Activity", self.project_activity)
        project_activity.completed_qty = (project_activity.completed_qty or 0) + self.qty_completed

        if project_activity.target_qty:
            project_activity.progress = (project_activity.completed_qty / project_activity.target_qty) * 100
        else:
            project_activity.progress = 0

        project_activity.save(ignore_permissions=True)
        frappe.db.commit()

        # --- 2. Update the Task linked in the Project Activity ---
        if project_activity.task:
            task = frappe.get_doc("Task", project_activity.task)
            totals = frappe.db.sql(
                """
                SELECT SUM(target_qty), SUM(completed_qty)
                FROM `tabProject Activity`
                WHERE task = %s
                """,
                (project_activity.task,)
            )[0]
            total_target = totals[0] or 0
            total_completed = totals[1] or 0

            if total_target:
                task.progress = (total_completed / total_target) * 100
            else:
                task.progress = 0

            task.save(ignore_permissions=True)
            frappe.db.commit()

            # --- 3. Update the Project linked in the Task ---
            if task.project:
                project = frappe.get_doc("Project", task.project)
                tasks = frappe.get_all("Task", filters={"project": task.project}, fields=["progress"])

                if tasks:
                    avg_progress = sum([t.progress for t in tasks]) / len(tasks)
                else:
                    avg_progress = 0

                project.percent_complete = avg_progress
                project.save(ignore_permissions=True)
                frappe.db.commit()

    def cancel_update_project_activity(self):
        # Ensure a Project Activity is linked
        if not self.project_activity:
            frappe.throw("Project Activity is not linked")

        # --- 1. Reverse update on the linked Project Activity ---
        project_activity = frappe.get_doc("Project Activity", self.project_activity)
        project_activity.completed_qty = (project_activity.completed_qty or 0) - self.qty_completed

        # Prevent negative values
        if project_activity.completed_qty < 0:
            project_activity.completed_qty = 0

        if project_activity.target_qty:
            project_activity.progress = (project_activity.completed_qty / project_activity.target_qty) * 100
        else:
            project_activity.progress = 0

        project_activity.save(ignore_permissions=True)
        frappe.db.commit()

        # --- 2. Update the Task linked in the Project Activity ---
        if project_activity.task:
            task = frappe.get_doc("Task", project_activity.task)
            totals = frappe.db.sql(
                """
                SELECT SUM(target_qty), SUM(completed_qty)
                FROM `tabProject Activity`
                WHERE task = %s
                """,
                (project_activity.task,)
            )[0]
            total_target = totals[0] or 0
            total_completed = totals[1] or 0

            if total_target:
                task.progress = (total_completed / total_target) * 100
            else:
                task.progress = 0

            task.save(ignore_permissions=True)
            frappe.db.commit()

            # --- 3. Update the Project linked in the Task ---
            if task.project:
                project = frappe.get_doc("Project", task.project)
                tasks = frappe.get_all("Task", filters={"project": task.project}, fields=["progress"])

                if tasks:
                    avg_progress = sum([t.progress for t in tasks]) / len(tasks)
                else:
                    avg_progress = 0

                project.percent_complete = avg_progress
                project.save(ignore_permissions=True)
                frappe.db.commit()

    def update_activity_performance_to_date(self):
        """Retrieves the current progress from the linked Project Activity
        and updates the 'performance_to_date' field in this document."""
        if not self.project_activity:
            frappe.throw("Project Activity is not linked")

        project_activity = frappe.get_doc("Project Activity", self.project_activity)
        # Update the field in this document with the current progress from Project Activity
        self.db_set("performance_to_date", project_activity.progress)
