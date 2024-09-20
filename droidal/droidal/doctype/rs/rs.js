// Copyright (c) 2024, droidal and contributors
// For license information, please see license.txt

frappe.ui.form.on('RS', {
	before_save: function(frm) {
		const formData = frm.doc
		// const jsonString = JSON.stringify(formData);
		console.log((formData))
		 frappe.call({
		 	method: "droidal.droidal.doctype.rs.rs.patient_status",
		 	args:{
		 		all_values : formData
		 	},
		 	callback:function(r){
		 		if (r.message === true){
		 			console.log("done")
		 		}
		 	}
		 })
	}
});
