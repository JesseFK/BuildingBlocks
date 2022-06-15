//Maya ASCII 2020 scene
//Name: square_template.ma
//Last modified: Tue, May 31, 2022 08:16:07 PM
//Codeset: 1252
requires maya "2020";
createNode transform -n "square_template";
	rename -uid "5AA72A83-4981-3B53-46A6-16A4A772DF94";
createNode nurbsCurve -n "square_templateShape" -p "square_template";
	rename -uid "F048B730-471C-2BEE-6A71-3FAF4574F447";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		1 4 0 no 3
		5 0 1.4142135623730949 2.8284271247461898 4.2426406871192848 5.6568542494923797
		
		5
		-0.50518874717056672 0.50518874717056661 2.6809599707155735e-16
		-0.50518874717056661 -0.50518874717056672 -2.2434887155612003e-16
		0.50518874717056661 -0.50518874717056672 -2.6809599707155735e-16
		0.50518874717056672 0.50518874717056661 2.2434887155611998e-16
		-0.50518874717056661 0.50518874717056672 2.6809599707155735e-16
		;
// End of square_template.ma
