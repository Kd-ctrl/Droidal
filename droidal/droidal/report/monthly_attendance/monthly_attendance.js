// Copyright (c) 2024, droidal and contributors
// For license information, please see license.txt
/* eslint-disable */
frappe.query_reports["Monthly Attendance"] = {
    filters: [
        {
            fieldname: "month",
            label: __("Month"),
            fieldtype: "Data",
            default: frappe.datetime.nowdate().slice(0, 7),  // YYYY-MM format
            reqd: 1
        }
    ]
};