function myFunction() {
	let fname = {{ data['firstname']|tojson }};
	let lname = {{ data['lastname']|tojson }};
                 alert (lname + "This is an alert dialog box"); 
       }

