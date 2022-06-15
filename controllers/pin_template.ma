//Maya ASCII 2020 scene
//Name: pin_template.ma
//Last modified: Tue, May 31, 2022 08:16:07 PM
//Codeset: 1252
requires maya "2020";
createNode transform -n "pin_template";
	rename -uid "AE80A574-492C-0A76-2894-3EA02F4D7DE3";
createNode nurbsCurve -n "pin_templateShape" -p "pin_template";
	rename -uid "BCF8F0C2-463B-23A2-F647-B6BE20981FA7";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		1 5 0 no 3
		6 0 1 2 3 4 5
		6
		0 0 0
		-3.7240250393518641e-17 0.30408972137474044 1.3504296408883418e-16
		0.10136324045824677 0.40545296183298729 1.8005728545177892e-16
		-6.2067083989197736e-17 0.50681620229123414 2.2507160681472366e-16
		-0.10136324045824688 0.40545296183298729 1.8005728545177892e-16
		-3.7240250393518641e-17 0.30408972137474044 1.3504296408883418e-16
		;
// End of pin_template.ma
