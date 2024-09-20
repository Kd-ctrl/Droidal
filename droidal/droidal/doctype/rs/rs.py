# Copyright (c) 2024, droidal and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class RS(Document):
	pass


class test(Document):
	pass

@frappe.whitelist()
def patient_status(all_values):
    print(all_values)