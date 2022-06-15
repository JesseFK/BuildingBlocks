//Maya ASCII 2020 scene
//Name: remap_box_template.ma
//Last modified: Tue, May 31, 2022 08:16:07 PM
//Codeset: 1252
requires maya "2020";
createNode transform -n "remap_box_template";
	rename -uid "DAC26948-48D7-F0B0-B4F7-7CB0DD88DB41";
createNode nurbsCurve -n "remap_box_templateShape" -p "remap_box_template";
	rename -uid "7966EA89-4AA7-48CB-CDA8-DBAB9873B592";
	setAttr -k off ".v";
	setAttr ".ovdt" 2;
	setAttr ".ove" yes;
	setAttr ".cc" -type "nurbsCurve" 
		1 7 0 no 3
		8 0 1 2 3 4 5 6 7
		8
		-1 0 1
		-1 0 -1
		1 0 -1
		1 0 1
		-1 0 1
		-1 0 2
		1 0 2
		1 0 1
		;
// End of remap_box_template.ma
