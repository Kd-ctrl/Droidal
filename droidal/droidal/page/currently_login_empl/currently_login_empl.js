frappe.pages['currently-login-empl'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Active Employees',
		single_column: true
	});
}