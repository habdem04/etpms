import frappe
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
            
        project_activity = frappe.get_doc("Project Activity", self.project_activity)
        mtype = project_activity.get("measurement_type")
        target_qty = project_activity.target_qty or 0

        # For Increasing and Decreasing, we sum the completed qty.
        # For Constant, use only the current day's completed quantity.
        if mtype in ["Increasing", "Decreasing"]:
            prev_completed = project_activity.completed_qty or 0
            new_completed = prev_completed + self.qty_completed
        elif mtype == "Constant":
            new_completed = self.qty_completed
        else:
            new_completed = (project_activity.completed_qty or 0) + self.qty_completed

        # Calculate progress based on measurement type
        if target_qty == 0 or new_completed == 0:
            progress = 0
        else:
            if mtype == "Increasing":
                progress = (new_completed / target_qty) * 100
            elif mtype == "Decreasing":
                progress = (target_qty / new_completed) * 100
            elif mtype == "Constant":
                progress = (new_completed / target_qty) * 100
            else:
                progress = (new_completed / target_qty) * 100

        project_activity.completed_qty = new_completed
        project_activity.progress = progress
        project_activity.save(ignore_permissions=True)
        frappe.db.commit()

        self.update_task_and_project(project_activity)

    def cancel_update_project_activity(self):
        # Ensure a Project Activity is linked
        if not self.project_activity:
            frappe.throw("Project Activity is not linked")
            
        project_activity = frappe.get_doc("Project Activity", self.project_activity)
        mtype = project_activity.get("measurement_type")
        target_qty = project_activity.target_qty or 0

        # For Increasing and Decreasing, subtract the current log's qty.
        # For Constant, reset to 0 (since it's an independent value).
        if mtype in ["Increasing", "Decreasing"]:
            prev_completed = project_activity.completed_qty or 0
            new_completed = prev_completed - self.qty_completed
            if new_completed < 0:
                new_completed = 0
        elif mtype == "Constant":
            new_completed = 0
        else:
            new_completed = (project_activity.completed_qty or 0) - self.qty_completed

        if target_qty == 0 or new_completed == 0:
            progress = 0
        else:
            if mtype == "Increasing":
                progress = (new_completed / target_qty) * 100
            elif mtype == "Decreasing":
                progress = (target_qty / new_completed) * 100
            elif mtype == "Constant":
                progress = (new_completed / target_qty) * 100
            else:
                progress = (new_completed / target_qty) * 100

        project_activity.completed_qty = new_completed
        project_activity.progress = progress
        project_activity.save(ignore_permissions=True)
        frappe.db.commit()

        self.update_task_and_project(project_activity)

    def update_task_and_project(self, project_activity):
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
        self.db_set("performance_to_date", project_activity.progress)
