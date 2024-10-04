// Copyright (c) 2024, droidal and contributors
// For license information, please see license.txt
frappe.ui.form.on('Employee Checkinout', {
	onload:async function(frm){
		frappe.call({
		method:"droidal.droidal.component.hrms_customize.current_status",
		callback:function(r){
			frm.set_value('current_status', r.message);
			frm.save();
		}
		})
		
	}



})


frappe.ui.form.on('Employee Checkinout', {
	check_in_out:async function(frm){
		frappe.call({
			method:"droidal.droidal.component.hrms_customize.checkin_out",
			callback:function(r){
				if (r.message == "IN"){
					frappe.msgprint("Checked In Successfully");
					frm.set_value('current_status', r.message);
					frm.save();
				}
				else if (r.message == "OUT"){
					frappe.msgprint("Checked Out Successfully");
					frm.set_value('current_status', r.message);
					frm.save();
				}
			}
		})
	}
});
