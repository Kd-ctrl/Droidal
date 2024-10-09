// document.addEventListener('DOMContentLoaded', function () {
//     function hideElements(selector) {
//         var currentUser = frappe.boot.user.name;


//         if (currentUser !== 'Administrator') {
//             var intervalId = setInterval(function () {
//                 var elements = document.querySelectorAll(selector);
//                 if (elements.length > 0) {
//                     elements.forEach(function (el) {
//                         el.style.display = 'none';
//                     });
//                     clearInterval(intervalId); 
//                 }
//             }, 5); 
//         }
//     }

//     const selectors = [

//         'button[data-label="Edit"]',
//         'button[data-label="Create%20Workspace"]',
//         ".custom-actions.hidden-xs.hidden-md"
//     ];

//     selectors.forEach(hideElements);
// });